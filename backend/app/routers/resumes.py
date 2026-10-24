import os
import shutil
import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Resume, JobPosting, User
from app.schemas.resume import ResumeOut
from app.services.parser import extract_text, parse_resume
from app.core.deps import get_current_user
from app.models.models import MatchScore
from app.schemas.match import RankedCandidate
from app.services.matcher import score_resume

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024
router = APIRouter(prefix="/jobs/{job_id}/resumes", tags=["resumes"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
DOCUMENT_FAILURE_DETAIL = (
    "Resume processing failed. Upload a valid, readable PDF or DOCX file."
)
STORAGE_FAILURE_DETAIL = "Resume could not be stored. Try again."


def _mark_resume_failed(db: Session, resume_id: int, reason: str) -> None:
    failed_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if failed_resume is None:
        return
    failed_resume.status = "failed"
    failed_resume.failure_reason = reason
    db.commit()


def _owned_job(db: Session, job_id: int, recruiter_id: int) -> JobPosting:
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == recruiter_id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


def _candidate_name(parsed_data: str | None) -> str | None:
    if not parsed_data:
        return None
    try:
        parsed = json.loads(parsed_data)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        name = parsed.get("name")
        return name if isinstance(name, str) else None
    return None


@router.post("/", response_model=ResumeOut)
def upload_resume(
    job_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _owned_job(db, job_id, current_user.id)

    original_filename = file.filename or ""
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large (max 5MB)")

    existing = db.query(Resume).filter(
        Resume.job_id == job_id, Resume.filename == original_filename
    ).first()
    if existing and existing.status != "failed":
        raise HTTPException(
            400, f"A resume named '{original_filename}' was already uploaded for this job"
        )

    safe_filename = f"{job_id}_{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, safe_filename)

    if existing is not None:
        resume = existing
        resume.status = "processing"
        resume.failure_reason = None
        resume.raw_text = None
        resume.parsed_data = None
    else:
        resume = Resume(
            job_id=job_id,
            filename=original_filename,
            status="processing",
        )
        db.add(resume)
    db.commit()
    db.refresh(resume)

    try:
        with open(save_path, "wb") as stored_file:
            shutil.copyfileobj(file.file, stored_file)

        raw_text = extract_text(save_path)
        parsed = parse_resume(raw_text)

        resume.raw_text = raw_text
        resume.parsed_data = json.dumps(parsed)
        resume.status = "done"
        resume.failure_reason = None
        db.commit()
        db.refresh(resume)
        return resume
    except HTTPException:
        raise
    except (OSError, SQLAlchemyError) as exc:
        logger.exception("Resume storage failed for resume_id=%s", resume.id)
        db.rollback()
        try:
            Path(save_path).unlink(missing_ok=True)
        except OSError:
            logger.exception("Could not remove failed resume file for resume_id=%s", resume.id)
        _mark_resume_failed(db, resume.id, STORAGE_FAILURE_DETAIL)
        raise HTTPException(status_code=500, detail=STORAGE_FAILURE_DETAIL) from exc
    except Exception as exc:
        logger.exception("Resume processing failed for resume_id=%s", resume.id)
        db.rollback()
        try:
            Path(save_path).unlink(missing_ok=True)
        except OSError:
            logger.exception("Could not remove failed resume file for resume_id=%s", resume.id)
        _mark_resume_failed(db, resume.id, DOCUMENT_FAILURE_DETAIL)
        raise HTTPException(status_code=422, detail=DOCUMENT_FAILURE_DETAIL) from exc


@router.get("/", response_model=list[ResumeOut])
def list_resumes(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _owned_job(db, job_id, current_user.id)
    return db.query(Resume).filter(Resume.job_id == job_id).all()


@router.post("/{resume_id}/reparse", response_model=ResumeOut)
def reparse_resume(
    job_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _owned_job(db, job_id, current_user.id)

    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.job_id == job_id).first()
    if not resume:
        raise HTTPException(404, "Resume not found")

    parsed = parse_resume(resume.raw_text or "")
    resume.parsed_data = json.dumps(parsed)
    resume.status = "done"
    resume.failure_reason = None
    db.commit()
    db.refresh(resume)

    return ResumeOut.model_validate(resume)


@router.get(
    "/rankings",
    response_model=list[RankedCandidate],
    summary="Rank resumes by semantic similarity",
    description=(
        "Scores each completed resume against the job description using semantic similarity. "
        "Structured skills, experience, and education criteria are not included in this score. "
        "Resumes that are still processing or failed to parse are omitted."
    ),
)
def rank_resumes(
    job_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _owned_job(db, job_id, current_user.id)

    resumes = db.query(Resume).filter(
        Resume.job_id == job_id, Resume.status == "done"
    ).all()

    results = []
    for resume in resumes:
        score_value = score_resume(job.description, resume.raw_text or "")

        existing = db.query(MatchScore).filter(MatchScore.resume_id == resume.id).first()
        if existing:
            existing.overall_score = score_value
        else:
            db.add(MatchScore(resume_id=resume.id, overall_score=score_value))

        results.append(RankedCandidate(
            resume_id=resume.id,
            filename=resume.filename,
            candidate_name=_candidate_name(resume.parsed_data),
            overall_score=score_value,
        ))

    db.commit()
    results.sort(key=lambda r: r.overall_score, reverse=True)

    return results[offset : offset + limit]
