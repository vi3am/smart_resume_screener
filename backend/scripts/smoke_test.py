"""End-to-end smoke test against a RUNNING backend, using only fake CVs.

Usage (from backend/, server running):  python scripts/smoke_test.py [--base-url http://localhost:8000]
It leaves a test user and job in the database. Run `python -m app.seed` afterwards to reset.
"""
import argparse
import io
import os
import sys
import uuid

import httpx
from docx import Document

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PASSWORD = "Smoke-Test-123!"
SCORE_KEYS = ["overall_score", "skills_score", "experience_score", "education_score", "semantic_score"]

MARKETING = [
    "Jordan Sample", "Marketing Coordinator", "Experience",
    "Marketing Coordinator, Sample Company  Jan 2022 - Dec 2024",
    "Planned and ran social media and content creation campaigns, tracked campaign results, "
    "and worked with designers and the sales team.",
    "Wrote weekly content, kept campaign planning calendars and improved communication across teams.",
    "Education", "Bachelor of Arts in Communication, Sample University",
    "Skills", "Social Media, Content Creation, Campaign Planning, Communication, Teamwork",
]
DEVELOPER = [
    "Casey Example", "Backend Developer", "Experience",
    "Backend Developer, Example Tech  2021 - 2024",
    "Built REST APIs with Python and FastAPI, designed PostgreSQL schemas and wrote automated tests.",
    "Education", "Bachelor of Science in Computer Science, Example University",
    "Skills", "Python, FastAPI, PostgreSQL, Docker, Git",
]
OFFICE = [
    "Riley Sample", "Office Assistant", "Experience",
    "Office Assistant, Sample Office  2023 - 2024",
    "Answered phones, filed documents and scheduled meetings for a small team.",
    "Education", "High School Diploma",
    "Skills", "Microsoft Office, Filing, Scheduling",
]


def make_docx(lines):
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    args = ap.parse_args()
    uid = uuid.uuid4().hex[:6]
    failures: list[str] = []

    def check(name, ok, detail=""):
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"   [{detail}]" if not ok and detail else ""))
        if not ok:
            failures.append(name)

    with httpx.Client(base_url=args.base_url, timeout=180) as http:
        try:
            health = http.get("/")
        except httpx.ConnectError:
            print("Cannot reach the backend. Start it: uvicorn main:app --reload --reload-dir app")
            return 1
        check("health endpoint", health.status_code == 200 and health.json().get("status") == "ok", health.text)

        def new_user(tag):
            r = http.post("/auth/register", json={"email": f"smoke_{tag}_{uid}@example.com", "password": PASSWORD})
            return r, {"Authorization": f"Bearer {r.json().get('access_token', '')}"}

        r, auth = new_user("owner")
        check("register returns an access token", r.status_code == 200 and "access_token" in r.json(), r.text)
        if failures:
            return 1

        job = http.post("/jobs/", headers=auth, json={
            "title": "Marketing Coordinator",
            "description": "We are looking for a Marketing Coordinator to plan and run social media and "
                        "content campaigns. You will work with designers and the sales team and track results.",
            "required_skills": ["Social Media", "Content Creation", "Campaign Planning", "Communication", "Teamwork"],
            "min_years_experience": 1, "min_education_level": "bachelor",
        })
        check("create job with structured fields", job.status_code in (200, 201), job.text)
        if job.status_code not in (200, 201):
            return 1
        job_id = job.json()["id"]

        files = [("files", (f"marketing_{uid}.docx", make_docx(MARKETING), DOCX)),
                 ("files", (f"developer_{uid}.docx", make_docx(DEVELOPER), DOCX)),
                 ("files", (f"office_{uid}.docx", make_docx(OFFICE), DOCX))]
        up = http.post(f"/jobs/{job_id}/resumes/batch", headers=auth, files=files)
        check("batch upload of 3 DOCX files", up.status_code == 200 and up.json().get("done") == 3, up.text)

        print("\n(the first scoring call loads the embedding model and can take a minute)")
        run_res = http.post(f"/jobs/{job_id}/scoring-runs/", headers=auth)
        check("create scoring run returns 201", run_res.status_code == 201, run_res.text)
        if run_res.status_code == 201:
            run = run_res.json()
            rows = run["results"]
            check("run stores the weights used", set(run["weights"]) == {"skills", "experience", "education", "semantic"})
            check("three ranked results", [x["rank"] for x in rows] == [1, 2, 3])
            overall = [x["overall_score"] for x in rows]
            check("results sorted by overall score", overall == sorted(overall, reverse=True))
            check("every component is between 0 and 100",
                  all(0 <= x[k] <= 100 for x in rows for k in SCORE_KEYS))
            check("matched and missing skills are lists",
                  all(isinstance(x["matched_skills"], list) and isinstance(x["missing_skills"], list) for x in rows))
            check("the marketing CV ranks first", rows[0]["filename"].startswith("marketing_"), rows[0]["filename"])
            print("\nrank  file                    overall skills  exp  edu  sem   missing")
            for x in rows:
                print(f"{x['rank']:>4}  {x['filename']:<22} {x['overall_score']:7.1f} {x['skills_score']:6.1f} "
                      f"{x['experience_score']:5.1f}{x['education_score']:5.1f}{x['semantic_score']:5.1f}   "
                      f"{', '.join(x['missing_skills'])}")
            print()
            latest = http.get(f"/jobs/{job_id}/scoring-runs/latest", headers=auth)
            check("latest run is the one just created", latest.status_code == 200 and latest.json()["id"] == run["id"])

        print("\nFailure cases")
        mixed = http.post(f"/jobs/{job_id}/resumes/batch", headers=auth, files=[
            ("files", (f"notes_{uid}.txt", b"hello", "text/plain")),
            ("files", (f"extra_{uid}.docx", make_docx(OFFICE), DOCX))])
        statuses = [x["status"] for x in mixed.json().get("results", [])] if mixed.status_code == 200 else []
        check("unsupported file fails, the valid one still succeeds", statuses == ["failed", "done"], mixed.text)

        corrupt = http.post(f"/jobs/{job_id}/resumes/batch", headers=auth,
                            files=[("files", (f"corrupt_{uid}.pdf", os.urandom(2000), "application/pdf"))])
        check("corrupt PDF is reported as failed, not a server error",
              corrupt.status_code == 200 and corrupt.json()["results"][0]["status"] == "failed", corrupt.text[:200])

        too_many = http.post(f"/jobs/{job_id}/resumes/batch", headers=auth,
                             files=[("files", (f"extra{i}_{uid}.docx", make_docx(OFFICE), DOCX)) for i in range(21)])
        check("21 files in one request are rejected with 400", too_many.status_code == 400, too_many.text[:200])

        check("no token gives 401", http.get("/jobs/").status_code == 401)

        _, other = new_user("other")
        check("another recruiter gets 404 for this job's results",
              http.get(f"/jobs/{job_id}/scoring-runs/latest", headers=other).status_code == 404)

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: {failures}")
        return 1
    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())