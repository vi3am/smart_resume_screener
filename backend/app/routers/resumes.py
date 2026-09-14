import os
import shutil
import json
import uuid
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Resume, JobPosting, User
from app.schemas.resume import ResumeOut
from app.services.file_utils import build_stored_filename
from app.services.parser import extract_text, parse_resume
from app.core.deps import get_current_user
from app.models.models import MatchScore
from app.schemas.match import RankedCandidate
from app.services.matcher import score_resume

MAX_FILE_SIZE = 5 * 1024 * 1024  
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
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    file.file.seek(0, 2)         
    size = file.file.tell()
    file.file.seek(0)             # reset pointer back to start — CRITICAL, or the file reads as empty later
    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 5MB)")    
    
    

    # Duplicate check (keep your existing logic here if already added)
    existing = db.query(Resume).filter(
        Resume.job_id == job_id, Resume.filename == file.filename
    ).first()
    if existing:
        raise HTTPException(400, f"A resume named '{file.filename}' was already uploaded for this job")

    # SECURITY: never use the user-supplied filename in the actual file path.
    # Generate a random, safe filename for disk storage; keep the original
    # only as a display value in the database.
    safe_filename = f"{job_id}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    raw_text = extract_text(save_path)
    parsed = parse_resume(raw_text)

    resume = Resume(
        job_id=job_id,
        filename=file.filename,      # original name, safe to store as text
        raw_text=raw_text,
        parsed_data=json.dumps(parsed),
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


@router.get("/rankings", response_model=list[RankedCandidate])
def rank_resumes(
    job_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")

    resumes = db.query(Resume).filter(Resume.job_id == job_id).all()

    results = []
    for resume in resumes:
        score_value = score_resume(job.description, resume.raw_text or "")

        existing = db.query(MatchScore).filter(MatchScore.resume_id == resume.id).first()
        if existing:
            existing.overall_score = score_value
        else:
            db.add(MatchScore(resume_id=resume.id, overall_score=score_value))

        parsed = json.loads(resume.parsed_data) if resume.parsed_data else {}
        results.append(RankedCandidate(
            resume_id=resume.id,
            filename=resume.filename,
            candidate_name=parsed.get("name"),
            overall_score=score_value,
            skills_score=None,
            experience_score=None,
        ))

    db.commit()
    results.sort(key=lambda r: r.overall_score, reverse=True)

    # Apply pagination AFTER sorting, so page boundaries respect rank order
    return results[offset : offset + limit]

