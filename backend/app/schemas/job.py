from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.core.education import EducationLevel


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    min_years_experience: int = Field(default=0, ge=0, le=50)
    min_education_level: EducationLevel = "high_school"

    @field_validator("title", "description")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field must not be blank")
        return value

    @field_validator("required_skills")
    @classmethod
    def clean_skills(cls, v: list[str]) -> list[str]:
        seen, cleaned = set(), []
        for skill in v:
            skill = skill.strip()
            if skill and skill.lower() not in seen:
                seen.add(skill.lower())
                cleaned.append(skill)
        return cleaned


class JobOut(BaseModel):
    id: int
    title: str
    description: str
    required_skills: list[str]
    min_years_experience: int
    min_education_level: str
    recruiter_id: int
    created_at: datetime

    class Config:
        from_attributes = True