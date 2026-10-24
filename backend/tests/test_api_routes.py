import subprocess
import sys
import uuid
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.models.models import JobPosting, Resume, User
from app.services.parser import extract_text
from main import app


client = TestClient(app)


def make_docx(path: str, paragraphs: list[str]) -> str:
    doc = Document()
    for paragraph in paragraphs:
        doc.add_paragraph(paragraph)
    doc.save(path)
    return path


def register_login(email: str, password: str = "Pass123!", full_name: str = "Tester"):
    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert register_response.status_code == 200, register_response.text
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def test_auth_and_job_resume_flow(monkeypatch, tmp_path):
    email = f"smoke_{uuid.uuid4().hex[:8]}@example.com"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr("app.routers.resumes.UPLOAD_DIR", str(upload_dir))

    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "Pass123!", "full_name": "Smoke Tester"},
    )
    assert register_response.status_code == 200, register_response.text
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "Pass123!"},
        headers=headers,
    )
    assert login_response.status_code == 200, login_response.text

    job_response = client.post(
        "/jobs/",
        json={
            "title": "Python Developer",
            "description": "Build APIs with FastAPI and SQLAlchemy",
            "required_skills": ["python", "fastapi", "sql"],
        },
        headers=headers,
    )
    assert job_response.status_code == 200, job_response.text
    job_id = job_response.json()["id"]

    empty_job_response = client.post(
        "/jobs/",
        json={"title": "Empty Job", "description": "No resumes yet", "required_skills": ["none"]},
        headers=headers,
    )
    assert empty_job_response.status_code == 200, empty_job_response.text
    empty_job_id = empty_job_response.json()["id"]

    resume_path = tmp_path / "john_smith.docx"
    make_docx(
        str(resume_path),
        [
            "John Smith",
            "john.smith@example.com",
            "+1 555 123 4567",
            "Skills: python, fastapi, sql, docker",
        ],
    )

    with resume_path.open("rb") as resume_file:
        upload_response = client.post(
            f"/jobs/{job_id}/resumes/",
            files={"file": ("john_smith.docx", resume_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=headers,
        )
    assert upload_response.status_code == 200, upload_response.text
    resume_id = upload_response.json()["id"]
    assert isinstance(upload_response.json()["parsed_data"], dict)

    list_resumes_response = client.get(f"/jobs/{job_id}/resumes/", headers=headers)
    assert list_resumes_response.status_code == 200, list_resumes_response.text
    assert any(item["id"] == resume_id for item in list_resumes_response.json())

    reparse_response = client.post(f"/jobs/{job_id}/resumes/{resume_id}/reparse", headers=headers)
    assert reparse_response.status_code == 200, reparse_response.text
    assert isinstance(reparse_response.json()["parsed_data"], dict)

    rankings_response = client.get(f"/jobs/{job_id}/resumes/rankings", headers=headers)
    assert rankings_response.status_code == 200, rankings_response.text
    assert isinstance(rankings_response.json(), list)

    delete_with_resume_response = client.delete(f"/jobs/{job_id}", headers=headers)
    assert delete_with_resume_response.status_code == 400
    assert "Cannot delete job" in delete_with_resume_response.json()["detail"]

    delete_empty_job_response = client.delete(f"/jobs/{empty_job_id}", headers=headers)
    assert delete_empty_job_response.status_code == 200, delete_empty_job_response.text
    assert delete_empty_job_response.json()["deleted"] is True


def test_authentication_contracts():
    email = f"auth_{uuid.uuid4().hex[:8]}@example.com"

    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": "Pass123!", "full_name": "Auth User"},
    )
    assert register_response.status_code == 200, register_response.text
    assert "access_token" in register_response.json()

    duplicate_response = client.post(
        "/auth/register",
        json={"email": email, "password": "Pass123!", "full_name": "Auth User"},
    )
    assert duplicate_response.status_code == 400

    short_password_response = client.post(
        "/auth/register",
        json={"email": f"short_{uuid.uuid4().hex[:8]}@example.com", "password": "short", "full_name": "Short"},
    )
    assert short_password_response.status_code == 422

    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "Pass123!"},
    )
    assert login_response.status_code == 200, login_response.text

    bad_login_response = client.post(
        "/auth/login",
        json={"email": email, "password": "WrongPass!"},
    )
    assert bad_login_response.status_code == 401

    protected_response = client.get("/jobs/")
    assert protected_response.status_code == 401


def test_job_posting_structured_fields_and_isolation():
    recruiter_email = f"jobs_{uuid.uuid4().hex[:8]}@example.com"
    recruiter_headers = register_login(recruiter_email)

    job_response = client.post(
        "/jobs/",
        json={
            "title": "Python Developer",
            "description": "Build APIs with FastAPI and SQLAlchemy",
            "required_skills": ["python", "fastapi", "sql"],
            "min_years_experience": 3,
            "min_education_level": "bachelor",
        },
        headers=recruiter_headers,
    )
    assert job_response.status_code == 200, job_response.text
    payload = job_response.json()
    assert payload["required_skills"] == ["python", "fastapi", "sql"]
    assert payload["min_years_experience"] == 3
    assert payload["min_education_level"] == "bachelor"

    invalid_education_response = client.post(
        "/jobs/",
        json={
            "title": "Bad Education",
            "description": "Bad category",
            "required_skills": ["python"],
            "min_years_experience": 2,
            "min_education_level": "invalid",
        },
        headers=recruiter_headers,
    )
    assert invalid_education_response.status_code == 422

    negative_years_response = client.post(
        "/jobs/",
        json={
            "title": "Bad Experience",
            "description": "Negative years",
            "required_skills": ["python"],
            "min_years_experience": -1,
            "min_education_level": "high_school",
        },
        headers=recruiter_headers,
    )
    assert negative_years_response.status_code == 422

    old_style_string_response = client.post(
        "/jobs/",
        json={
            "title": "Bad Skills",
            "description": "Wrong contract",
            "required_skills": "python, fastapi",
            "min_years_experience": 1,
            "min_education_level": "high_school",
        },
        headers=recruiter_headers,
    )
    assert old_style_string_response.status_code == 422

    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    other_headers = register_login(other_email)

    other_read = client.get(f"/jobs/{payload['id']}", headers=other_headers)
    assert other_read.status_code == 404

    other_edit = client.put(
        f"/jobs/{payload['id']}",
        json={
            "title": "Edited by Other",
            "description": "Should fail",
            "required_skills": ["forbidden"],
            "min_years_experience": 1,
            "min_education_level": "high_school",
        },
        headers=other_headers,
    )
    assert other_edit.status_code == 404


def test_resume_upload_status_and_ranking_contracts(monkeypatch, tmp_path):
    recruiter_email = f"resume_{uuid.uuid4().hex[:8]}@example.com"
    headers = register_login(recruiter_email)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr("app.routers.resumes.UPLOAD_DIR", str(upload_dir))
    score_inputs = []

    def semantic_score(job_description, resume_text):
        score_inputs.append((job_description, resume_text))
        return 90.0 if "python" in resume_text.lower() else 10.0

    monkeypatch.setattr(
        "app.routers.resumes.score_resume",
        semantic_score,
    )

    job_response = client.post(
        "/jobs/",
        json={
            "title": "Data Engineer",
            "description": "Build data pipelines and APIs using Python, SQL, and cloud tools.",
            "required_skills": ["python", "sql", "aws"],
            "min_years_experience": 2,
            "min_education_level": "bachelor",
        },
        headers=headers,
    )
    assert job_response.status_code == 200, job_response.text
    job_id = job_response.json()["id"]

    valid_docx = tmp_path / "valid_resume.docx"
    make_docx(
        str(valid_docx),
        [
            "Alex Engineer",
            "alex@example.com",
            "Skills: python, sql, aws, fastapi",
            "Experience: 2020 - 2022 building APIs and ETL pipelines.",
            "Education: Bachelor of Science",
        ],
    )
    with valid_docx.open("rb") as f:
        upload_response = client.post(
            f"/jobs/{job_id}/resumes/",
            files={"file": ("alex_engineer.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=headers,
        )
    assert upload_response.status_code == 200, upload_response.text
    assert upload_response.json()["status"] == "done"
    parsed = upload_response.json()["parsed_data"]
    assert parsed["email"] == "alex@example.com"
    assert "years_experience" in parsed
    assert parsed["years_experience"] > 0
    assert parsed["education_level"] == "bachelor"
    assert "education_in_progress" in parsed

    invalid_type = client.post(
        f"/jobs/{job_id}/resumes/",
        files={"file": ("bad.txt", b"not a real document", "text/plain")},
        headers=headers,
    )
    assert invalid_type.status_code == 400

    big_file = b"x" * (5 * 1024 * 1024 + 1)
    oversized = client.post(
        f"/jobs/{job_id}/resumes/",
        files={"file": ("large.pdf", big_file, "application/pdf")},
        headers=headers,
    )
    assert oversized.status_code == 400

    list_response = client.get(f"/jobs/{job_id}/resumes/", headers=headers)
    assert list_response.status_code == 200, list_response.text
    resumes = list_response.json()
    assert resumes and all("status" in item for item in resumes)

    rankings_response = client.get(f"/jobs/{job_id}/resumes/rankings", headers=headers)
    assert rankings_response.status_code == 200, rankings_response.text
    rankings = rankings_response.json()
    assert isinstance(rankings, list)
    assert len(rankings) >= 1
    assert rankings[0]["overall_score"] >= rankings[-1]["overall_score"]
    assert "skills_score" not in rankings[0]
    assert "experience_score" not in rankings[0]
    assert all(
        description == job_response.json()["description"]
        for description, _ in score_inputs
    )
    assert any("Alex Engineer" in resume_text for _, resume_text in score_inputs)

    paginated = client.get(f"/jobs/{job_id}/resumes/rankings?limit=1&offset=0", headers=headers)
    assert paginated.status_code == 200, paginated.text
    assert len(paginated.json()) == 1

    irrelevant_docx = tmp_path / "irrelevant_resume.docx"
    make_docx(
        str(irrelevant_docx),
        [
            "Taylor Chef",
            "chef@example.com",
            "Skills: cooking, baking, restaurant service, menu planning",
            "Experience: 6 years in restaurants and catering",
        ],
    )
    with irrelevant_docx.open("rb") as f:
        irrelevant_upload = client.post(
            f"/jobs/{job_id}/resumes/",
            files={"file": ("cook.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=headers,
        )
    assert irrelevant_upload.status_code == 200, irrelevant_upload.text

    refreshed = client.get(f"/jobs/{job_id}/resumes/rankings", headers=headers)
    assert refreshed.status_code == 200
    ranked = refreshed.json()
    ranked_by_id = {item["resume_id"]: item["overall_score"] for item in ranked}
    relevant_id = upload_response.json()["id"]
    irrelevant_id = irrelevant_upload.json()["id"]
    assert ranked_by_id[relevant_id] > ranked_by_id[irrelevant_id]


def test_resume_processing_failure_records_status_and_removes_file(monkeypatch, tmp_path):
    recruiter_headers = register_login(f"upload_failure_{uuid.uuid4().hex[:8]}@example.com")
    job_response = client.post(
        "/jobs/",
        json={"title": "Developer", "description": "Python", "required_skills": ["python"]},
        headers=recruiter_headers,
    )
    assert job_response.status_code == 200, job_response.text

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr("app.routers.resumes.UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(
        "app.routers.resumes.extract_text",
        lambda _: (_ for _ in ()).throw(ValueError("invalid test document")),
    )

    response = client.post(
        f"/jobs/{job_response.json()['id']}/resumes/",
        files={"file": ("broken.docx", b"not a DOCX", "application/octet-stream")},
        headers=recruiter_headers,
    )

    assert response.status_code == 422
    assert list(upload_dir.iterdir()) == []
    db = SessionLocal()
    try:
        failed_resume = (
            db.query(Resume)
            .filter(Resume.filename == "broken.docx")
            .order_by(Resume.id.desc())
            .first()
        )
        assert failed_resume is not None
        assert failed_resume.status == "failed"
        assert failed_resume.failure_reason
    finally:
        db.close()


def test_seed_script_runs_cleanly():
    backend_dir = Path(__file__).resolve().parents[1]
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, "-m", "app.seed"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Seeded recruiter id=" in result.stdout
        assert "Seeded job id=" in result.stdout

        db = SessionLocal()
        try:
            assert db.query(User).count() == 1
            assert db.query(JobPosting).count() == 1
        finally:
            db.close()
