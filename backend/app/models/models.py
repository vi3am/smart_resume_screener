from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.sql import func
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
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)  # Text = unlimited length, unlike String
    requirements = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # The Python-side convenience link back to the User object.
    recruiter = relationship("User", back_populates="job_postings")

    # Same pattern as above - lets us write job.resumes to get all resumes
    # submitted for this job posting.
    resumes = relationship("Resume", back_populates="job_posting")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String, nullable=True)
    file_path = Column(String, nullable=False)  # where the uploaded file lives on disk
    raw_text = Column(Text, nullable=True)       # extracted text - filled in during Week 6
    match_score = Column(Integer, nullable=True) # filled in during Week 7-8 (matching engine)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # THIS is the foreign key - links this resume to one specific job posting.
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)

    job_posting = relationship("JobPosting", back_populates="resumes")