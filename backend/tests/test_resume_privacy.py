import os
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.config import settings
from app.database import SessionLocal
from app.models.models import MatchScore, Resume, ScoringResult
from app.routers import resumes as resume_routes
from app.services import scoring_runs as scoring_runs_service
from app.services.resume_retention import (
    delete_expired_resumes,
    delete_expired_upload_files,
)
from main import app


client = TestClient(app)
PASSWORD = "Privacy-Test-Password-123!"


def register(email: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_job(headers: dict[str, str]) -> int:
    response = client.post(
        "/jobs/",
        headers=headers,
        json={
            "title": "Privacy Test Role",
            "description": "A test role for resume deletion coverage.",
            "required_skills": ["python"],
            "min_years_experience": 0,
            "min_education_level": "high_school",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_upload_checks_mime_and_removes_temporary_file(monkeypatch, tmp_path):
    headers = register(f"privacy_upload_{uuid.uuid4().hex}@example.com")
    job_id = create_job(headers)
    upload_dir = tmp_path / "private_uploads"
    monkeypatch.setattr(resume_routes, "UPLOAD_DIR", upload_dir)
    extracted_paths = []

    def fake_extract(path):
        assert isinstance(path, str)
        assert os.path.isfile(path)
        extracted_paths.append(path)
        return "A candidate with Python experience. " * 4

    monkeypatch.setattr(resume_routes, "extract_text", fake_extract)
    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Test Candidate"})

    wrong_mime = client.post(
        f"/jobs/{job_id}/resumes/",
        headers=headers,
        files={"file": ("wrong.pdf", b"%PDF-1.4\ncontent", "text/plain")},
    )
    assert wrong_mime.status_code == 400
    assert "MIME type" in wrong_mime.json()["detail"]
    assert not upload_dir.exists()

    wrong_content = client.post(
        f"/jobs/{job_id}/resumes/",
        headers=headers,
        files={"file": ("wrong.pdf", b"not a PDF", "application/pdf")},
    )
    assert wrong_content.status_code == 400
    assert not upload_dir.exists()

    uploaded = client.post(
        f"/jobs/{job_id}/resumes/",
        headers=headers,
        files={"file": ("../private/candidate.pdf", b"%PDF-1.4\ncontent", "application/pdf")},
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["filename"] == "candidate.pdf"
    assert len(extracted_paths) == 1
    assert not list(upload_dir.iterdir())
    assert os.stat(upload_dir).st_mode & 0o777 == 0o700


def test_resume_delete_is_owner_scoped_and_removes_related_scores(monkeypatch):
    owner_headers = register(f"privacy_owner_{uuid.uuid4().hex}@example.com")
    other_headers = register(f"privacy_other_{uuid.uuid4().hex}@example.com")
    job_id = create_job(owner_headers)

    monkeypatch.setattr(
        resume_routes,
        "extract_text",
        lambda _: "A candidate with Python experience. " * 4,
    )
    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Test Candidate"})
    upload = client.post(
        f"/jobs/{job_id}/resumes/",
        headers=owner_headers,
        files={"file": ("candidate.pdf", b"%PDF-1.4\ncontent", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    resume_id = upload.json()["id"]

    def fake_score_cv(*_args, **_kwargs):
        from types import SimpleNamespace

        return SimpleNamespace(
            skills=0.8,
            experience=0.8,
            education=0.8,
            semantic=0.8,
            overall=0.8,
            matched_skills=["python"],
            missing_skills=[],
        )

    monkeypatch.setattr(scoring_runs_service, "score_cv", fake_score_cv)
    scoring = client.post(
        f"/jobs/{job_id}/scoring-runs/",
        headers=owner_headers,
    )
    assert scoring.status_code == 201, scoring.text

    denied = client.delete(
        f"/jobs/{job_id}/resumes/{resume_id}",
        headers=other_headers,
    )
    assert denied.status_code == 404

    deleted = client.delete(
        f"/jobs/{job_id}/resumes/{resume_id}",
        headers=owner_headers,
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True}

    db = SessionLocal()
    try:
        assert db.query(Resume).filter(Resume.id == resume_id).first() is None
        assert db.query(MatchScore).filter(MatchScore.resume_id == resume_id).first() is None
        assert db.query(ScoringResult).filter(ScoringResult.resume_id == resume_id).first() is None
    finally:
        db.close()


def test_docx_validation_rejects_non_word_archives():
    import io

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("not-a-word-document.txt", "no resume")
    payload.seek(0)
    upload = UploadFile(
        filename="not-a-docx.docx",
        file=payload,
        headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
    )

    try:
        resume_routes._validate_document(upload, ".docx")
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("A generic ZIP archive must not pass DOCX validation")

    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    payload.seek(0)
    valid_upload = UploadFile(
        filename="valid.docx",
        file=payload,
        headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
    )
    resume_routes._validate_document(valid_upload, ".docx")


def test_retention_deletes_expired_resume_and_its_scoring_data(monkeypatch):
    headers = register(f"privacy_expiry_{uuid.uuid4().hex}@example.com")
    job_id = create_job(headers)
    monkeypatch.setattr(
        resume_routes,
        "extract_text",
        lambda _: "A candidate with Python experience. " * 4,
    )
    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Expired Candidate"})
    upload = client.post(
        f"/jobs/{job_id}/resumes/",
        headers=headers,
        files={"file": ("expired.pdf", b"%PDF-1.4\ncontent", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    resume_id = upload.json()["id"]

    db = SessionLocal()
    try:
        resume = db.query(Resume).filter(Resume.id == resume_id).one()
        resume.uploaded_at = datetime.now(timezone.utc) - timedelta(
            days=settings.RESUME_RETENTION_DAYS + 1
        )
        db.add(MatchScore(resume_id=resume_id, overall_score=0.8))
        db.commit()

        assert delete_expired_resumes(db) == 1
        db.commit()
        assert db.query(Resume).filter(Resume.id == resume_id).first() is None
        assert db.query(MatchScore).filter(MatchScore.resume_id == resume_id).first() is None
        assert db.query(ScoringResult).filter(ScoringResult.resume_id == resume_id).first() is None
    finally:
        db.close()


def test_stale_file_cleanup_only_removes_expired_app_uploads(tmp_path):
    now = datetime.now(timezone.utc)
    old_upload = tmp_path / "12_0123456789abcdef0123456789abcdef.pdf"
    recent_upload = tmp_path / "12_1123456789abcdef0123456789abcdef.docx"
    unrelated = tmp_path / "keep-me.pdf"
    for path in (old_upload, recent_upload, unrelated):
        path.write_bytes(b"test")
    old_timestamp = (now - timedelta(days=settings.RESUME_RETENTION_DAYS + 1)).timestamp()
    os.utime(old_upload, (old_timestamp, old_timestamp))
    os.utime(unrelated, (old_timestamp, old_timestamp))

    assert delete_expired_upload_files(tmp_path, now=now) == 1
    assert not old_upload.exists()
    assert recent_upload.exists()
    assert unrelated.exists()
