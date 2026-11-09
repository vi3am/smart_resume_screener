import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.routers import resumes as resume_routes
from app.services import scoring_runs as scoring_runs_service
from main import app

client = TestClient(app)


def register_user(email: str, password: str = "Test-Pass-123!"):
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(email: str, password: str = "Test-Pass-123!"):
    token = register_user(email, password=password)
    return {"Authorization": f"Bearer {token}"}


def create_job(headers, title: str = "Data Engineer", description: str = "Build and maintain ETL pipelines."):
    response = client.post(
        "/jobs/",
        json={
            "title": title,
            "description": description,
            "required_skills": ["python", "sql"],
            "min_years_experience": 3,
            "min_education_level": "bachelor",
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_job_routes_crud_and_access_control():
    owner_email = f"jobs_owner_{uuid.uuid4().hex}@example.com"
    other_email = f"jobs_other_{uuid.uuid4().hex}@example.com"
    owner_headers = auth_headers(owner_email)
    other_headers = auth_headers(other_email)

    job = create_job(owner_headers, title="Senior Data Engineer")
    assert job["title"] == "Senior Data Engineer"
    assert job["required_skills"] == ["python", "sql"]

    list_response = client.get("/jobs/", headers=owner_headers)
    assert list_response.status_code == 200, list_response.text
    assert any(item["id"] == job["id"] for item in list_response.json())

    forbidden = client.get(f"/jobs/{job['id']}", headers=other_headers)
    assert forbidden.status_code == 404, forbidden.text

    updated = client.put(
        f"/jobs/{job['id']}",
        json={
            "title": "Lead Data Engineer",
            "description": "Lead ETL and analytics projects across the company.",
            "required_skills": ["python", "sql", "dbt"],
            "min_years_experience": 5,
            "min_education_level": "master",
        },
        headers=owner_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Lead Data Engineer"
    assert updated.json()["required_skills"] == ["python", "sql", "dbt"]

    deleted = client.delete(f"/jobs/{job['id']}", headers=owner_headers)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json() == {"deleted": True}

    missing = client.get(f"/jobs/{job['id']}", headers=owner_headers)
    assert missing.status_code == 404, missing.text


def test_resume_routes_upload_reparse_and_ranking(monkeypatch):
    owner_email = f"resumes_owner_{uuid.uuid4().hex}@example.com"
    other_email = f"resumes_other_{uuid.uuid4().hex}@example.com"
    owner_headers = auth_headers(owner_email)
    other_headers = auth_headers(other_email)
    job = create_job(owner_headers, title="Python Engineer")

    monkeypatch.setattr(resume_routes, "extract_text", lambda _: "Alice Example has 4 years of Python and SQL experience")
    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Alice Example", "years_experience": 4})
    monkeypatch.setattr(resume_routes, "score_resume", lambda *_args, **_kwargs: 0.92)

    upload = client.post(
        f"/jobs/{job['id']}/resumes/",
        headers=owner_headers,
        files={"file": ("alice.pdf", b"%PDF-1.4\nAlice Example", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text
    uploaded = upload.json()
    assert uploaded["filename"] == "alice.pdf"
    assert uploaded["status"] == "done"
    resume_id = uploaded["id"]

    listing = client.get(f"/jobs/{job['id']}/resumes/", headers=owner_headers)
    assert listing.status_code == 200, listing.text
    assert any(item["id"] == resume_id for item in listing.json())

    denied = client.post(
        f"/jobs/{job['id']}/resumes/",
        headers=other_headers,
        files={"file": ("blocked.pdf", b"%PDF-1.4\nBlocked", "application/pdf")},
    )
    assert denied.status_code == 404, denied.text

    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Alice Updated", "years_experience": 6})
    reparsed = client.post(f"/jobs/{job['id']}/resumes/{resume_id}/reparse", headers=owner_headers)
    assert reparsed.status_code == 200, reparsed.text
    assert reparsed.json()["status"] == "done"

    rankings = client.get(f"/jobs/{job['id']}/resumes/rankings", headers=owner_headers)
    assert rankings.status_code == 200, rankings.text
    result = rankings.json()
    assert len(result) == 1
    assert result[0]["resume_id"] == resume_id
    assert result[0]["candidate_name"] == "Alice Updated"
    assert result[0]["overall_score"] == 0.92


def test_scoring_routes_create_and_fetch_latest(monkeypatch):
    owner_email = f"scoring_owner_{uuid.uuid4().hex}@example.com"
    owner_headers = auth_headers(owner_email)
    job = create_job(owner_headers, title="Backend Engineer", description="Build resilient Python services with SQL and cloud APIs.")

    monkeypatch.setattr(resume_routes, "extract_text", lambda _: "Python, SQL, docker, microservices")
    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Bob Candidate", "years_experience": 5})
    upload = client.post(
        f"/jobs/{job['id']}/resumes/",
        headers=owner_headers,
        files={"file": ("bob.pdf", b"%PDF-1.4\nBob Candidate", "application/pdf")},
    )
    assert upload.status_code == 200, upload.text

    def fake_score_cv(*_args, **_kwargs):
        return SimpleNamespace(
            skills=0.9,
            experience=0.85,
            education=0.8,
            semantic=0.75,
            overall=0.82,
            matched_skills=["python", "sql"],
            missing_skills=[],
        )

    monkeypatch.setattr(scoring_runs_service, "score_cv", fake_score_cv)

    created = client.post(f"/jobs/{job['id']}/scoring-runs/", headers=owner_headers)
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["job_id"] == job["id"]
    assert payload["method"] == "hybrid_v1"
    assert len(payload["results"]) == 1
    assert payload["results"][0]["filename"] == "bob.pdf"

    latest = client.get(f"/jobs/{job['id']}/scoring-runs/latest", headers=owner_headers)
    assert latest.status_code == 200, latest.text
    assert latest.json()["id"] == payload["id"]
