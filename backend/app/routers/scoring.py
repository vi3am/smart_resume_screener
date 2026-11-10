from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.models import JobPosting, Resume, ScoringRun, User
from app.schemas.scoring import ScoringRunOut
from app.services.scoring_runs import create_run, run_out

router = APIRouter(prefix="/jobs/{job_id}/scoring-runs", tags=["scoring"])


def _owned_job(db: Session, job_id: int, user: User) -> JobPosting:
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/", response_model=ScoringRunOut, status_code=201)
def create_scoring_run(job_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    job = _owned_job(db, job_id, current_user)
    resumes = (db.query(Resume)
            .filter(Resume.job_id == job_id, Resume.status == "done")
            .order_by(Resume.id).all())
    if not resumes:
        raise HTTPException(400, "No processed résumés to score for this job")
    return run_out(db, create_run(db, job, resumes))


@router.get("/latest", response_model=ScoringRunOut)
def latest_scoring_run(job_id: int, db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)):
    job = _owned_job(db, job_id, current_user)
    run = (db.query(ScoringRun).filter(ScoringRun.job_id == job_id)
            .order_by(ScoringRun.id.desc()).first())
    if not run:
        raise HTTPException(404, "No scoring run yet for this job")
    if job.updated_at and run.created_at < job.updated_at:
        raise HTTPException(404, "Job requirements changed. Run scoring again.")
    return run_out(db, run)