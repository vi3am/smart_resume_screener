"""Upload up to 20 résumés in one request. Each file uses the single-file upload route."""
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.models import JobPosting, User
from app.routers.resumes import upload_resume

MAX_FILES = 20

router = APIRouter(prefix="/jobs/{job_id}/resumes", tags=["resumes"])


class BatchItem(BaseModel):
    filename: str
    status: Literal["done", "failed"]
    resume_id: int | None = None
    failure_reason: str | None = None


class BatchOut(BaseModel):
    done: int
    failed: int
    results: list[BatchItem]


@router.post("/batch", response_model=BatchOut)
def upload_batch(
    job_id: int,
    files: list[UploadFile] | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id, JobPosting.recruiter_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if not files:
        raise HTTPException(400, "No files were sent")
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Too many files: send at most {MAX_FILES} per request")

    results: list[BatchItem] = []
    for file in files:
        name = file.filename or "unnamed"
        try:
            resume = upload_resume(job_id=job_id, file=file, db=db, current_user=current_user)
        except HTTPException as exc:
            db.rollback()
            results.append(BatchItem(filename=name, status="failed", failure_reason=str(exc.detail)))
            continue
        results.append(BatchItem(
            filename=name,
            status=getattr(resume, "status", None) or "done",
            resume_id=getattr(resume, "id", None),
            failure_reason=getattr(resume, "failure_reason", None),
        ))

    return BatchOut(
        done=sum(1 for r in results if r.status == "done"),
        failed=sum(1 for r in results if r.status == "failed"),
        results=results,
    )