import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import MatchScore, Resume, ScoringResult

UPLOAD_NAME = re.compile(r"\d+_[0-9a-f]{32}\.(?:pdf|docx)\Z")


def delete_resume_data(db: Session, resume: Resume) -> None:
    db.query(ScoringResult).filter(
        ScoringResult.resume_id == resume.id
    ).delete(synchronize_session=False)
    db.query(MatchScore).filter(
        MatchScore.resume_id == resume.id
    ).delete(synchronize_session=False)
    db.delete(resume)


def delete_expired_resumes(db: Session, now: datetime | None = None) -> int:
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(days=settings.RESUME_RETENTION_DAYS)
    expired = db.query(Resume).filter(Resume.uploaded_at < cutoff).all()
    for resume in expired:
        delete_resume_data(db, resume)
    return len(expired)


def delete_expired_upload_files(upload_dir: Path, now: datetime | None = None) -> int:
    current_time = now or datetime.now(timezone.utc)
    cutoff_timestamp = (
        current_time - timedelta(days=settings.RESUME_RETENTION_DAYS)
    ).timestamp()
    if not upload_dir.exists():
        return 0

    deleted = 0
    for path in upload_dir.iterdir():
        if not UPLOAD_NAME.fullmatch(path.name) or not path.is_file():
            continue
        if path.stat().st_mtime < cutoff_timestamp:
            path.unlink()
            deleted += 1
    return deleted
