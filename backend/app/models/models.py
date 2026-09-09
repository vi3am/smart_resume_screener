from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, func
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
    required_skills = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recruiter = relationship("User", back_populates="job_postings")
    resumes = relationship("Resume", back_populates="job")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_data = Column(Text, nullable=True)   # JSON string: name, email, phone, skills, education, experience
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobPosting", back_populates="resumes")
    score = relationship("MatchScore", back_populates="resume", uselist=False)


class MatchScore(Base):
    __tablename__ = "match_scores"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), unique=True, nullable=False)
    overall_score = Column(Float, nullable=False)
    skills_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    scored_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="score")