"""
Reset and seed the database with one recruiter, one job, and a note on where
resumes come from. Run manually — never imported by the app itself.

Usage: python -m app.seed
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.models import User, JobPosting, Resume, MatchScore, ScoringRun, ScoringResult
from app.core.security import hash_password


def reset_data(db: Session) -> None:
    # Children first, to respect foreign keys before parents are removed.
    db.query(ScoringResult).delete()
    db.query(ScoringRun).delete()
    db.query(MatchScore).delete()
    db.query(Resume).delete()
    db.query(JobPosting).delete()
    db.query(User).delete()
    db.commit()


def seed(db: Session) -> None:
    recruiter = User(
        email="recruiter@example.com",
        hashed_password=hash_password("SeedPass123"),
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

    print(f"Seeded recruiter id={recruiter.id} (recruiter@example.com / SeedPass123)")
    print(f"Seeded job id={job.id}: {job.title}")
    print("Upload resumes to this job through /docs to continue the vertical slice.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        reset_data(db)
        seed(db)
    finally:
        db.close()