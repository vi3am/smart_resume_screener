from pydantic import BaseModel
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: str | None = None

class JobOut(BaseModel):
    id: int
    title: str
    description: str
    required_skills: str | None
    recruiter_id: int
    created_at: datetime

    class Config:
        from_attributes = True