from pydantic import BaseModel
from datetime import datetime

class ParsedResumeData(BaseModel):
    """Shape of the JSON stored in Resume.parsed_data — not a DB table itself."""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] | None = None
    education: list[str] | None = None
    experience: list[str] | None = None

class ResumeOut(BaseModel):
    id: int
    job_id: int
    filename: str
    parsed_data: ParsedResumeData | None = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ResumeUploadResponse(BaseModel):
    id: int
    filename: str
    parsed: ParsedResumeData