from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, func
from sqlalchemy import CheckConstraint, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from app.core.education import EDUCATION_LEVELS
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False, server_default="recruiter")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job_postings = relationship("JobPosting", back_populates="recruiter")


class JobPosting(Base):
    __tablename__ = "job_postings"
    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(ARRAY(Text), nullable=False, server_default=text("'{}'::text[]"))
    min_years_experience = Column(Integer, nullable=False, server_default="0")
    min_education_level = Column(String, nullable=False, server_default="high_school")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())   

    recruiter = relationship("User", back_populates="job_postings")
    resumes = relationship("Resume", back_populates="job")
    
    __table_args__ = (
        CheckConstraint("min_years_experience >= 0", name="ck_job_postings_min_years_nonneg"),
        CheckConstraint(
            "min_education_level IN (" + ", ".join(f"'{l}'" for l in EDUCATION_LEVELS) + ")",
            name="ck_job_postings_min_education_level",
        ),
    )


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(Text, nullable=True)
    status = Column(String, nullable=False,server_default="processing")
    failure_reason = Column(Text,nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobPosting", back_populates="resumes")
    score = relationship("MatchScore", back_populates="resume", uselist=False)
    
    __table_args__ = (
        CheckConstraint("status IN ('processing', 'done', 'failed')", name="ck_resumes_status"),
    )


class MatchScore(Base):
    __tablename__ = "match_scores"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), unique=True, nullable=False)
    overall_score = Column(Float, nullable=False)
    skills_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    scored_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="score")
    
    
class ScoringRun(Base):
    __tablename__ = "scoring_runs"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String, nullable=False)
    weights = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ScoringResult(Base):
    __tablename__ = "scoring_results"

    id = Column(Integer, primary_key=True)
    scoring_run_id = Column(Integer, ForeignKey("scoring_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    skills_score = Column(Float, nullable=False)
    experience_score = Column(Float, nullable=False)
    education_score = Column(Float, nullable=False)
    semantic_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    matched_skills = Column(ARRAY(Text), nullable=False, server_default=text("'{}'::text[]"))
    missing_skills = Column(ARRAY(Text), nullable=False, server_default=text("'{}'::text[]"))

    __table_args__ = (
        UniqueConstraint("scoring_run_id", "resume_id", name="uq_scoring_results_run_resume"),
    )