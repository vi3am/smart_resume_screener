# Smart Resume Screener

A FastAPI + React app for creating job postings, uploading resumes, and ranking candidates against a job description.

## Tech stack

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL 16
- Auth: JWT
- Resume parsing: pdfplumber, python-docx, spaCy
- Matching: sentence-transformers
- Local infrastructure: Docker Compose

## Prerequisites

Install these before starting:

- Python 3.11+
- Node.js 18+
- npm
- Docker Desktop or Docker Engine
- Git

Verify versions:

```powershell
python --version
node --version
npm --version
docker --version
git --version
```

## 1) Clone the repository

```powershell
git clone <your-repo-url>
cd smart-resume-screener
```

## 2) Create the backend environment file

Create a file named `.env` inside `backend`:

```powershell
cd backend
@'
APP_NAME=Smart Resume Screener
DEBUG=True
JWT_SECRET_KEY=change-this-to-a-long-random-string
DATABASE_URL=postgresql://admin:random_password@localhost:5433/resume_screener
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
POSTGRES_USER=admin
POSTGRES_PASSWORD=random_password
POSTGRES_DB=resume_screener
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
'@ | Set-Content .env
```

Notes:

- The backend reads `backend/.env` automatically.
- Docker Compose also reads the same file and exposes PostgreSQL on port `5433`.
- If you change the Postgres password, reset the Docker database volume before reconnecting.

## 3) Start PostgreSQL with Docker

From the project root:

```powershell
cd ..
docker compose up -d db
```

Check the container:

```powershell
docker ps
```

You should see a container named `resume_screener_db`.

## 4) Create and activate a Python virtual environment

From the backend folder:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 5) Install backend dependencies

```powershell
pip install -r requirements-dev.txt
```

The spaCy English model is pinned in `requirements.txt` with a SHA-256 hash and is installed by the command above. Verify that the active environment can load the model used by resume parsing:

```powershell
python -c "import spacy; spacy.load('en_core_web_sm'); print('spaCy model ready')"
```

Do not remove or change the wheel's SHA-256 hash. Run this check in the same virtual environment that starts Uvicorn; the API loads this model for resume parsing.

## 6) Run database migrations

```powershell
alembic upgrade head
```

## 7) Start the backend

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open the API docs at:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## 8) Start the frontend

Open a second terminal and run:

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Then open:

- http://localhost:5173

The frontend expects the backend at `http://localhost:8000`.

## 9) Run tests

The API test suite includes a seed test that clears its database. Tests refuse to start unless `TEST_DATABASE_URL` points to a dedicated PostgreSQL database ending in `_test`; the test environment will not fall back to `backend/.env`.

Create the dedicated test database once:

```powershell
docker exec resume_screener_db psql -U admin -d postgres -c "CREATE DATABASE resume_screener_test;"
```

From the backend directory, set the test URL, migrate that database, and run the suite:

```powershell
$env:TEST_DATABASE_URL = "postgresql://admin:<password>@localhost:5433/resume_screener_test"
$env:DATABASE_URL = $env:TEST_DATABASE_URL
alembic upgrade head
python -m pytest tests -q
```

Replace `<password>` with your local PostgreSQL password. The test guard requires a database name ending in `_test`.
From the backend directory, `bash verify.sh` uses this same dedicated test database and runs `alembic upgrade head` before testing, so the migration check and API tests target the same schema.

## 10) Seed demo data

The seed command deletes existing records. It refuses to reset a database unless its name ends in `_test` or you explicitly set `ALLOW_DESTRUCTIVE_SEED=1`.

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
$env:ALLOW_DESTRUCTIVE_SEED = "1"
python -m app.seed
```

This resets the configured database and prints the seeded recruiter and job IDs. Do not use it against a production database.

## Ranking behavior

Resume rankings currently use semantic similarity between the job description and resume text only. The structured required-skills, experience, and education fields are not included in the score. The API returns only the overall score rather than placeholder component scores.

## Useful commands

### Start only the database

```powershell
docker compose up -d db
```

### Start backend only

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start frontend only

```powershell
cd frontend
npm run dev -- --host 0.0.0.0
```

### Reset the database

```powershell
docker compose down -v
docker compose up -d db
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

## Troubleshooting

### `password authentication failed for user "admin"`

This usually means the old PostgreSQL volume still contains an older password.

Run:

```powershell
docker compose down -v
docker compose up -d db
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

### `No module named pytest`

Install the development dependencies in the backend virtual environment:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest tests -q
```

### `ModuleNotFoundError` for spaCy model

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "import spacy; spacy.load('en_core_web_sm'); print('spaCy model ready')"
```

### Connection refused / database not reachable

Check the database container:

```powershell
docker ps
docker logs resume_screener_db
```

Then confirm the database URL is:

```text
postgresql://admin:random_password@localhost:5433/resume_screener
```

## Quick start summary

```powershell
cd smart-resume-screener
docker compose up -d db
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Then open:

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

## Notes

This project was written to work cleanly in a Windows PowerShell environment, but the same app also runs in macOS/Linux terminals using the equivalent Unix commands.