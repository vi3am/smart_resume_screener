import os
import shutil
import json
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Resume, JobPosting, User
from app.schemas.resume import ResumeOut
from app.services.parser import extract_text, parse_resume
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
    parsed = parse_resume(raw_text)

    resume = Resume(
        job_id=job_id,
        filename=file.filename,
        raw_text=raw_text,
        parsed_data=json.dumps(parsed)
        )
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


@router.post("/{resume_id}/reparse", response_model=ResumeOut)
def reparse_resume(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")

    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.job_id == job_id).first()
    if not resume:
        raise HTTPException(404, "Resume not found")

    parsed = parse_resume(resume.raw_text or "")
    resume.parsed_data = json.dumps(parsed)
    db.commit()
    db.refresh(resume)
    
    response = ResumeOut.model_validate(resume)
    response.parsed_data = parsed 
    return response