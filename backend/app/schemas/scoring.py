from datetime import datetime

from pydantic import BaseModel


class ScoredResumeOut(BaseModel):
    rank: int
    resume_id: int
    filename: str
    candidate_name: str | None
    overall_score: float
    skills_score: float
    experience_score: float
    education_score: float
    semantic_score: float
    matched_skills: list[str]
    missing_skills: list[str]


class ScoringRunOut(BaseModel):
    id: int
    job_id: int
    method: str
    weights: dict[str, float]
    created_at: datetime
    results: list[ScoredResumeOut]