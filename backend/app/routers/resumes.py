import os
import shutil
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Resume, JobPosting, User
from app.schemas.resume import ResumeOut
from app.services.parser import extract_text
from app.core.deps import get_current_user

router = APIRouter(prefix="/jobs/{job_id}/resumes", tags=["resumes"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

@router.post("/", response_model=ResumeOut)
def upload_resume(
    job_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Confirm the job exists AND belongs to this recruiter
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    save_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    raw_text = extract_text(save_path)

    resume = Resume(job_id=job_id, filename=file.filename, raw_text=raw_text)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/", response_model=list[ResumeOut])
def list_resumes(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")

    return db.query(Resume).filter(Resume.job_id == job_id).all()