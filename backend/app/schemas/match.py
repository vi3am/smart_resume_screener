from pydantic import BaseModel
from datetime import datetime

class MatchScoreOut(BaseModel):
    id: int
    resume_id: int
    overall_score: float
    skills_score: float | None
    experience_score: float | None
    scored_at: datetime

    class Config:
        from_attributes = True

class RankedCandidate(BaseModel):
    """Resume fields and semantic-only overall score returned by the ranking endpoint."""
    resume_id: int
    filename: str
    candidate_name: str | None
    overall_score: float

    class Config:
        from_attributes = True