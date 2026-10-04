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
pip install -r requirements.txt
```

If the spaCy English model is not installed:

```powershell
python -m spacy download en_core_web_sm
```

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

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest tests -q
```

## 10) Seed demo data

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.seed
```

This resets the local demo data and prints the seeded recruiter and job IDs.

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

Use the venv in the backend folder:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest tests -q
```

### `ModuleNotFoundError` for spaCy model

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m spacy download en_core_web_sm
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