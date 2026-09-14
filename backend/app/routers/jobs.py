from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import JobPosting, User, Resume
from app.schemas.job import JobCreate, JobOut
from app.core.deps import get_current_user


router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/", response_model=JobOut)
def create_job(job: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_job = JobPosting(**job.dict(), recruiter_id=current_user.id)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

@router.get("/", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(JobPosting).filter(JobPosting.recruiter_id == current_user.id).all()

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job

@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: int, updates: JobCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(JobPosting).filter(JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    for key, value in updates.dict().items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")

    resume_count = db.query(Resume).filter(Resume.job_id == job_id).count()
    if resume_count > 0:
        raise HTTPException(
            400,
            f"Cannot delete job with {resume_count} resume(s) attached. Delete the resumes first."
        )

    db.delete(job)
    db.commit()
    return {"deleted": True}