from datetime import timedelta
import uuid

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.database import SessionLocal
from app.models.models import RefreshToken, User
from app.routers.auth import _token_hash
from main import app


client = TestClient(app)


def register(email: str, **extra):
    payload = {"email": email, "password": "Auth-Test-Password-123!", **extra}
    return client.post("/auth/register", json=payload)


def test_password_hashing_and_generic_login_failures():
    email = f"security_{uuid.uuid4().hex}@example.com"
    password = "Auth-Test-Password-123!"
    response = register(email)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type"}
    assert password not in response.text
    raw_refresh_token = response.cookies.get("refresh_token")
    assert raw_refresh_token
    set_cookie = response.headers["set-cookie"].lower()
    assert "httponly" in set_cookie and "samesite=strict" in set_cookie and "path=/auth" in set_cookie

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).one()
        assert user.hashed_password != password
        assert user.hashed_password.startswith("$2b$")
        refresh_row = db.query(RefreshToken).filter(
            RefreshToken.token_hash == _token_hash(raw_refresh_token)
        ).one()
        assert raw_refresh_token not in refresh_row.token_hash
    finally:
        db.close()

    wrong_password = client.post("/auth/login", json={"email": email, "password": "Wrong-Password-123!"})
    unknown_email = client.post(
        "/auth/login",
        json={"email": f"missing_{uuid.uuid4().hex}@example.com", "password": "Wrong-Password-123!"},
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {"detail": "Invalid credentials"}


def test_password_validation_and_role_input_rejected():
    email = f"escalation_{uuid.uuid4().hex}@example.com"
    too_long = client.post(
        "/auth/register",
        json={"email": email, "password": "a" * 73},
    )
    assert too_long.status_code == 422

    role_injection = register(email, role="admin", is_admin=True)
    assert role_injection.status_code == 422
    db = SessionLocal()
    try:
        assert db.query(User).filter(User.email == email).first() is None
    finally:
        db.close()


def test_expired_and_tampered_access_tokens_are_rejected():
    email = f"expired_{uuid.uuid4().hex}@example.com"
    assert register(email).status_code == 200
    expired = create_access_token({"sub": email}, expires_delta=timedelta(seconds=-1))

    expired_response = client.get("/jobs/", headers={"Authorization": f"Bearer {expired}"})
    assert expired_response.status_code == 401

    valid = client.post("/auth/login", json={"email": email, "password": "Auth-Test-Password-123!"}).json()["access_token"]
    tampered = f"{valid[:-1]}{'A' if valid[-1] != 'A' else 'B'}"
    tampered_response = client.get("/jobs/", headers={"Authorization": f"Bearer {tampered}"})
    assert tampered_response.status_code == 401


def test_refresh_rotation_reuse_detection_and_logout_revocation():
    email = f"refresh_{uuid.uuid4().hex}@example.com"
    initial_response = register(email)
    tokens = initial_response.json()
    initial_refresh = initial_response.cookies.get("refresh_token")
    assert initial_refresh

    rotated_response = client.post("/auth/refresh", cookies={"refresh_token": initial_refresh})
    assert rotated_response.status_code == 200
    rotated = rotated_response.json()
    assert rotated["access_token"] != tokens["access_token"]
    rotated_refresh = rotated_response.cookies.get("refresh_token")
    assert rotated_refresh and rotated_refresh != initial_refresh
    assert "refresh_token" not in rotated

    replay = client.post("/auth/refresh", cookies={"refresh_token": initial_refresh})
    assert replay.status_code == 401
    family_revoked = client.post("/auth/refresh", cookies={"refresh_token": rotated_refresh})
    assert family_revoked.status_code == 401

    fresh_login_response = client.post("/auth/login", json={"email": email, "password": "Auth-Test-Password-123!"})
    fresh_login = fresh_login_response.json()
    fresh_refresh = fresh_login_response.cookies.get("refresh_token")
    logout = client.post(
        "/auth/logout",
        cookies={"refresh_token": fresh_refresh},
    )
    assert logout.status_code == 200
    after_logout = client.post("/auth/refresh", cookies={"refresh_token": fresh_refresh})
    assert after_logout.status_code == 401

    expiring_response = register(f"refresh_expiry_{uuid.uuid4().hex}@example.com")
    expiring_token = expiring_response.cookies.get("refresh_token")
    db = SessionLocal()
    try:
        row = db.query(RefreshToken).filter(RefreshToken.token_hash == _token_hash(expiring_token)).one()
        row.expires_at -= timedelta(days=60)
        db.commit()
    finally:
        db.close()
    expired_refresh = client.post("/auth/refresh", cookies={"refresh_token": expiring_token})
    assert expired_refresh.status_code == 401


def test_unauthorized_and_cross_recruiter_requests_are_denied():
    no_token = client.get("/jobs/")
    assert no_token.status_code == 401

    owner_email = f"owner_{uuid.uuid4().hex}@example.com"
    other_email = f"other_{uuid.uuid4().hex}@example.com"
    owner_tokens = register(owner_email).json()
    other_tokens = register(other_email).json()
    other_job_response = client.post(
        "/jobs/",
        json={"title": "Private role", "description": "Owned by another recruiter"},
        headers={"Authorization": f"Bearer {other_tokens['access_token']}"},
    )
    assert other_job_response.status_code == 200
    other_job_id = other_job_response.json()["id"]

    # Even a validly signed token with a forged role claim still resolves identity
    # from the database and cannot cross the recruiter ownership boundary.
    forged_role_token = create_access_token({"sub": owner_email, "role": "admin"})
    denied = client.get(f"/jobs/{other_job_id}", headers={"Authorization": f"Bearer {forged_role_token}"})
    assert denied.status_code == 404

    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.email == owner_email).one()
        assert owner.role == "recruiter"
    finally:
        db.close()


def test_refresh_token_cannot_authenticate_protected_endpoint():
    email = f"refresh_auth_{uuid.uuid4().hex}@example.com"
    response = register(email)
    tokens = response.json()
    assert "refresh_token" not in tokens
    refresh_token = response.cookies.get("refresh_token")
    response = client.get("/jobs/", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 401
