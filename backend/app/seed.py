"""
Reset and seed the database with one recruiter, one job, and a note on where
resumes come from. Run manually — never imported by the app itself.

Usage: python -m app.seed
"""
import os
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.config import settings
from app.models.models import User, JobPosting, Resume, MatchScore, RefreshToken, ScoringRun, ScoringResult
from app.core.security import hash_password


def reset_data(db: Session) -> None:
    database_name = make_url(settings.DATABASE_URL).database or ""
    if (
        not database_name.endswith("_test")
        and os.environ.get("ALLOW_DESTRUCTIVE_SEED") != "1"
    ):
        raise RuntimeError(
            "Refusing to clear a non-test database. Set ALLOW_DESTRUCTIVE_SEED=1 "
            "to explicitly permit resetting this database."
        )

    # Children first, to respect foreign keys before parents are removed.
    db.query(ScoringResult).delete()
    db.query(ScoringRun).delete()
    db.query(MatchScore).delete()
    db.query(RefreshToken).delete()
    db.query(Resume).delete()
    db.query(JobPosting).delete()
    db.query(User).delete()
    db.commit()


def validate_seed_password(recruiter_password: str) -> None:
    if len(recruiter_password.encode("utf-8")) < 16:
        raise ValueError("SEED_RECRUITER_PASSWORD must be at least 16 UTF-8 bytes")
    if len(recruiter_password.encode("utf-8")) > 72:
        raise ValueError("SEED_RECRUITER_PASSWORD must be at most 72 UTF-8 bytes")


def seed(db: Session, recruiter_password: str) -> None:
    validate_seed_password(recruiter_password)
    recruiter = User(
        email="recruiter@example.com",
        hashed_password=hash_password(recruiter_password),
        full_name="Demo Recruiter",
    )
    db.add(recruiter)
    db.commit()
    db.refresh(recruiter)

    job = JobPosting(
        recruiter_id=recruiter.id,
        title="Mobile App Developer",
        description=(
            "We are seeking a Mobile App Developer to build and maintain modern "
            "Android applications. The ideal candidate has experience developing "
            "user-friendly mobile interfaces and integrating APIs."
        ),
        required_skills=["Kotlin", "Android", "Jetpack Compose", "REST API", "Git"],
        min_years_experience=1,
        min_education_level="associate",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    print(f"Seeded recruiter id={recruiter.id}")
    print(f"Seeded job id={job.id}: {job.title}")


if __name__ == "__main__":
    recruiter_password = os.environ.get("SEED_RECRUITER_PASSWORD")
    if not recruiter_password:
        raise SystemExit(
            "Set SEED_RECRUITER_PASSWORD to a unique password of at least 16 "
            "UTF-8 bytes before seeding."
        )
    try:
        validate_seed_password(recruiter_password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    db = SessionLocal()
    try:
        reset_data(db)
        seed(db, recruiter_password)
    finally:
        db.close()
