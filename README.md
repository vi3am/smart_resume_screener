# Smart Resume Screener

A full-stack app for creating job postings, uploading resumes, and matching candidates to a job description. The backend is FastAPI with PostgreSQL; the frontend is React and Vite.

## MVP workflow

- Create a job with its required skills, minimum experience, and education level.
- Upload up to 20 PDF or DOCX resumes per batch; each file is limited to 5 MB.
- Review extracted resume details, then run hybrid scoring to rank candidates and inspect each score component.
- Search results by candidate name, filename, or skill, or filter by minimum match score.
- Select candidates in the ranking table and export only the selected shortlist as CSV.

See [MVP scope and acceptance criteria](./MVP_ACCEPTANCE.md) for the current
scoring formula, skill-matching behavior, out-of-scope features, and test
evidence. The ranking is a review aid, not a hiring decision.

The frontend uses the authenticated job CRUD routes, resume batch/list/delete/
reparse routes, and the scoring-runs routes. A single resume is uploaded as a
one-file batch. The older semantic-only `GET /jobs/{job_id}/resumes/rankings`
route is intentionally not used by the UI; the dashboard uses the stored
four-component scoring-run API instead.

## Requirements

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+ and npm
- Docker with the Compose plugin
- Git

## Install

Clone the repository, then create the backend environment file:

```sh
git clone <repository-url>
cd smart-resume-screener
```

Create `backend/.env` with these values:

```dotenv
APP_NAME=Smart Resume Screener
DEBUG=True
JWT_SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=postgresql://admin:change-me@localhost:5433/resume_screener
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
RESUME_RETENTION_DAYS=180
POSTGRES_USER=admin
POSTGRES_PASSWORD=change-me
POSTGRES_DB=resume_screener
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

Use the same username, password, and database name in `DATABASE_URL` and the `POSTGRES_*` values. If the password contains URL-reserved characters, percent-encode it in `DATABASE_URL`. Keep `.env` local and do not commit secrets.

Start PostgreSQL from the repository root:

```sh
docker compose up -d db
```

Install the Python dependencies and migrate the database:

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
alembic upgrade head
```

The requirements install the pinned spaCy English model used by resume parsing. Resume matching downloads the `all-MiniLM-L6-v2` model on its first use, so the first match may take longer.

## Resume privacy and retention

Only the recruiter who owns a job can access or delete its resumes. PDF and DOCX uploads must have a matching extension, MIME type, and document structure; files are assigned random storage names, written with owner-only permissions, and removed after parsing. Extracted resume text and parsed candidate details remain in the database until the recruiter deletes them or the retention period expires.

The default retention period is 180 days and can be changed with `RESUME_RETENTION_DAYS`. Run the cleanup command daily from `backend/` (for example, schedule it with cron) so expired resume records, candidate details, scores, and stale upload files are removed:

```sh
.venv/bin/python -m app.cleanup_expired_resumes
```

Example daily cron entry (replace the path with the absolute backend directory):

```cron
0 3 * * * cd /path/to/smart-resume-screener/backend && .venv/bin/python -m app.cleanup_expired_resumes
```

Deleting a resume through `DELETE /jobs/{job_id}/resumes/{resume_id}` immediately removes its stored text, parsed details, and score rows. Seed data does not have a built-in password: set `SEED_RECRUITER_PASSWORD` to a unique password of at least 16 UTF-8 bytes before running `python -m app.seed`. Do not use real resumes without permission; use anonymized or synthetic demo data.

Install frontend packages in another terminal from the repository root:

```sh
cd frontend
npm ci
```

## Run locally

Start the backend from `backend/` with its virtual environment active:

```sh
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Start the frontend from `frontend/`:

```sh
npm run dev
```

Open the app at <http://localhost:5173>. The API docs are at <http://localhost:8000/docs>, and the API health endpoint is <http://localhost:8000/>.

## Stop services

Stop the frontend and backend with `Ctrl+C`. Stop PostgreSQL while keeping its data with:

```sh
docker compose stop db
```

To stop PostgreSQL and delete its local data volume, run `docker compose down -v` from the repository root.

## Windows PowerShell notes

Create and activate the backend virtual environment with:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If script activation is blocked, allow it for the current PowerShell process with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. The remaining Python commands are the same. Run the frontend commands from `frontend/` in a second terminal.
