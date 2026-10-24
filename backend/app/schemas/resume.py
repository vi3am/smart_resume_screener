import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ParsedResumeData(BaseModel):
    """Shape of the JSON stored in Resume.parsed_data — matches parse_resume()."""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] | None = None
    years_experience: float | None = None
    education_level: str | None = None
    education_in_progress: str | None = None


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    filename: str
    parsed_data: ParsedResumeData | None = None
    status: str
    failure_reason: str | None = None
    uploaded_at: datetime

    @field_validator("parsed_data", mode="before")
    @classmethod
    def decode_parsed_data(cls, value: object) -> object:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return value


class ResumeUploadResponse(BaseModel):
    id: int
    filename: str
    parsed: ParsedResumeData
