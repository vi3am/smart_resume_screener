"""Create and read stored scoring runs. Uses the same score_cv() that the evaluation harness uses."""
import json
from datetime import date

from sqlalchemy.orm import Session

from app.models.models import JobPosting, Resume, ScoringResult, ScoringRun
from app.schemas.scoring import ScoredResumeOut, ScoringRunOut
from app.services.scoring import DEFAULT_WEIGHTS, score_cv

METHOD = "hybrid_v1"
FIELD_KEYS = ("years_experience", "education_level", "education_in_progress")


def posting_dict(job: JobPosting) -> dict:
    return {
        "title": job.title,
        "description": job.description,
        "required_skills": list(job.required_skills or []),
        "min_years_experience": job.min_years_experience,
        "min_education_level": job.min_education_level,
    }


def _parsed(resume: Resume) -> dict:
    try:
        return json.loads(resume.parsed_data) if resume.parsed_data else {}
    except (TypeError, ValueError):
        return {}


def create_run(db: Session, job: JobPosting, resumes: list[Resume]) -> ScoringRun:
    posting = posting_dict(job)
    run = ScoringRun(job_id=job.id, method=METHOD, weights=dict(DEFAULT_WEIGHTS))
    db.add(run)
    db.flush()  # gives the run its id
    for resume in resumes:
        parsed = _parsed(resume)
        # CVs parsed before the field extraction existed have no fields; score_cv computes them then.
        fields = {k: parsed.get(k) for k in FIELD_KEYS} if "years_experience" in parsed else None
        r = score_cv(posting, resume.raw_text or "", fields=fields,
                     weights=DEFAULT_WEIGHTS, as_of=date.today())
        db.add(ScoringResult(
            scoring_run_id=run.id, resume_id=resume.id,
            skills_score=r.skills, experience_score=r.experience,
            education_score=r.education, semantic_score=r.semantic,
            overall_score=r.overall,
            matched_skills=r.matched_skills, missing_skills=r.missing_skills,
        ))
    db.commit()
    db.refresh(run)
    return run


def run_out(db: Session, run: ScoringRun) -> ScoringRunOut:
    rows = (
        db.query(ScoringResult, Resume)
        .join(Resume, Resume.id == ScoringResult.resume_id)
        .filter(ScoringResult.scoring_run_id == run.id)
        .order_by(ScoringResult.overall_score.desc(), Resume.id.asc())
        .all()
    )
    results = [
        ScoredResumeOut(
            rank=i, resume_id=res.id, filename=res.filename,
            candidate_name=_parsed(res).get("name"),
            overall_score=sr.overall_score, skills_score=sr.skills_score,
            experience_score=sr.experience_score, education_score=sr.education_score,
            semantic_score=sr.semantic_score,
            matched_skills=list(sr.matched_skills or []), missing_skills=list(sr.missing_skills or []),
        )
        for i, (sr, res) in enumerate(rows, start=1)
    ]
    return ScoringRunOut(id=run.id, job_id=run.job_id, method=run.method,
                        weights=run.weights, created_at=run.created_at, results=results)