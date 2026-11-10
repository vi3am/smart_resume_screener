import uuid

from fastapi.testclient import TestClient

from app.routers import resumes as resume_routes
from app.services.scan_check import SCANNED_MESSAGE, ScannedPdfError
from main import app

client = TestClient(app)
PASSWORD = "Test-Pass-123!"
CV_TEXT = "Alex Example knows Python well and has experience building services. " * 3


def make_job():
    email = f"batch_{uuid.uuid4().hex}@example.com"
    token = client.post("/auth/register", json={"email": email, "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    job = client.post("/jobs/", headers=headers, json={
        "title": "Test Role", "description": "Test description for batch uploads.",
        "required_skills": ["python"], "min_years_experience": 0, "min_education_level": "high_school",
    }).json()
    return job, headers


def pdf(name):
    return ("files", (name, b"%PDF-1.4\nfake", "application/pdf"))


def patch_parser(monkeypatch):
    monkeypatch.setattr(resume_routes, "extract_text", lambda _: CV_TEXT)
    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Alex Example"})


def test_batch_accepts_twenty_files(monkeypatch):
    patch_parser(monkeypatch)
    job, headers = make_job()
    res = client.post(f"/jobs/{job['id']}/resumes/batch", headers=headers,
                      files=[pdf(f"cv_{i}.pdf") for i in range(20)])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["done"] == 20 and body["failed"] == 0
    assert len(body["results"]) == 20
    assert all(
        result["status"] == "done"
        and result["resume_id"] is not None
        and result["failure_reason"] is None
        for result in body["results"]
    )


def test_batch_rejects_twenty_one_files(monkeypatch):
    patch_parser(monkeypatch)
    job, headers = make_job()
    res = client.post(f"/jobs/{job['id']}/resumes/batch", headers=headers,
                      files=[pdf(f"cv_{i}.pdf") for i in range(21)])
    assert res.status_code == 400
    assert "at most 20" in res.json()["detail"]


def test_batch_rejects_no_files(monkeypatch):
    job, headers = make_job()
    res = client.post(f"/jobs/{job['id']}/resumes/batch", headers=headers)
    assert res.status_code == 400


def test_batch_reports_scanned_pdf_as_failed_and_continues(monkeypatch):
    calls = {"n": 0}

    def fake_extract(_path):
        calls["n"] += 1
        if calls["n"] == 2:
            raise ScannedPdfError(SCANNED_MESSAGE)
        return CV_TEXT

    monkeypatch.setattr(resume_routes, "extract_text", fake_extract)
    monkeypatch.setattr(resume_routes, "parse_resume", lambda _: {"name": "Alex Example"})
    job, headers = make_job()
    res = client.post(f"/jobs/{job['id']}/resumes/batch", headers=headers,
                      files=[pdf("a.pdf"), pdf("scan.pdf"), pdf("c.pdf")])
    assert res.status_code == 200, res.text
    results = res.json()["results"]
    assert [r["status"] for r in results] == ["done", "failed", "done"]
    assert results[1]["resume_id"] is None
    assert "scanned" in (results[1]["failure_reason"] or "").lower()


def test_batch_continues_after_unsupported_file(monkeypatch):
    patch_parser(monkeypatch)
    job, headers = make_job()
    res = client.post(f"/jobs/{job['id']}/resumes/batch", headers=headers, files=[
        pdf("a.pdf"), ("files", ("notes.txt", b"hello", "text/plain")), pdf("c.pdf"),
    ])
    assert res.status_code == 200, res.text
    results = res.json()["results"]
    assert [r["status"] for r in results] == ["done", "failed", "done"]
    assert results[1]["failure_reason"]


def test_batch_for_someone_elses_job_is_404(monkeypatch):
    patch_parser(monkeypatch)
    job, _ = make_job()
    _, other_headers = make_job()
    res = client.post(f"/jobs/{job['id']}/resumes/batch", headers=other_headers, files=[pdf("a.pdf")])
    assert res.status_code == 404