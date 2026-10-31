from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.models import RefreshToken, User
from app.schemas.auth import LogoutResponse, Token, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


def _invalid_refresh() -> HTTPException:
    return HTTPException(status_code=401, detail="Invalid or expired refresh token")


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_token_pair(db: Session, user: User, family_id: str | None = None) -> dict[str, str]:
    raw_refresh_token = secrets.token_urlsafe(48)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_token_hash(raw_refresh_token),
        family_id=family_id or str(uuid.uuid4()),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    return {
        "access_token": create_access_token({"sub": user.email}),
        "refresh_token": raw_refresh_token,
    }


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        path="/auth",
    )


def _public_token_response(pair: dict[str, str], response: Response) -> dict[str, str]:
    _set_refresh_cookie(response, pair["refresh_token"])
    return {"access_token": pair["access_token"], "token_type": "bearer"}


def _revoke_family(db: Session, family_id: str, now: datetime) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.family_id == family_id,
        RefreshToken.revoked_at.is_(None),
    ).update({RefreshToken.revoked_at: now}, synchronize_session=False)


@router.post("/register", response_model=Token)
def register(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(400, "Email already registered")
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        full_name=user.full_name,
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(400, "Email already registered") from exc
    db.refresh(new_user)
    pair = _issue_token_pair(db, new_user)
    db.commit()
    return _public_token_response(pair, response)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    pair = _issue_token_pair(db, user)
    db.commit()
    return _public_token_response(pair, response)


@router.post("/refresh", response_model=Token)
def refresh_tokens(request: Request, response: Response, db: Session = Depends(get_db)):
    raw_refresh_token = request.cookies.get("refresh_token")
    if not raw_refresh_token:
        raise _invalid_refresh()

    now = datetime.now(timezone.utc)
    token_row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == _token_hash(raw_refresh_token))
        .with_for_update()
        .first()
    )
    if token_row is None:
        raise _invalid_refresh()
    if token_row.revoked_at is not None:
        # Reuse of a rotated token signals possible theft; invalidate its session family.
        _revoke_family(db, token_row.family_id, now)
        db.commit()
        raise _invalid_refresh()
    if token_row.expires_at <= now:
        token_row.revoked_at = now
        db.commit()
        raise _invalid_refresh()

    user = db.query(User).filter(User.id == token_row.user_id).first()
    if user is None:
        token_row.revoked_at = now
        db.commit()
        raise _invalid_refresh()

    pair = _issue_token_pair(db, user, family_id=token_row.family_id)
    token_row.revoked_at = now
    token_row.replaced_by_hash = _token_hash(pair["refresh_token"])
    db.commit()
    return _public_token_response(pair, response)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    raw_refresh_token = request.cookies.get("refresh_token")
    if raw_refresh_token:
        token_row = db.query(RefreshToken).filter(
            RefreshToken.token_hash == _token_hash(raw_refresh_token),
        ).first()
        if token_row is not None:
            _revoke_family(db, token_row.family_id, now)
            db.commit()
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="strict",
        path="/auth",
    )
    return {"revoked": True}
