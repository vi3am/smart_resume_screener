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

```bash
python3 --version
node --version
npm --version
docker --version
git --version
```

## 1) Clone the repository

```bash
git clone <your-repo-url>
cd smart-resume-screener
```

## 2) Configure backend environment

Create a backend `.env` file:

```bash
cd backend
cat > .env <<'EOF'
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
EOF
```

Notes:

- The backend loads environment variables from `backend/.env`.
- Docker Compose reads the same file and exposes PostgreSQL on port `5433`.
- If you change the password, reset the database volume before reconnecting.

## 3) Start PostgreSQL

From the project root:

```bash
cd ..
docker compose up -d db
```

Check that the container is running:

```bash
docker ps
```

You should see a PostgreSQL container named `resume_screener_db`.

## 4) Install backend dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If the spaCy English model is not already installed, run:

```bash
python -m spacy download en_core_web_sm
```

## 5) Run database migrations

From the backend directory:

```bash
source .venv/bin/activate
alembic upgrade head
```

## 6) Start the backend

From the backend directory:

```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 7) Start the frontend

Open a second terminal and run:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Then open:

- http://localhost:5173

The frontend expects the backend at `http://localhost:8000`.

## 8) Run tests

Backend tests:

```bash
cd backend
source .venv/bin/activate
python -m pytest tests -q
```

## 9) Seed demo data

From the backend directory:

```bash
source .venv/bin/activate
python -m app.seed
```

This resets the local seed data and prints a seeded recruiter and job ID.

## Useful commands

### Start just the database

```bash
docker compose up -d db
```

### Start backend only

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start frontend only

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

### Reset the DB completely

```bash
docker compose down -v
docker compose up -d db
cd backend
source .venv/bin/activate
alembic upgrade head
```

## Troubleshooting

### `password authentication failed for user "admin"`

This usually means your old PostgreSQL volume is still present with an older password.

Run:

```bash
docker compose down -v
docker compose up -d db
cd backend
source .venv/bin/activate
alembic upgrade head
```

### `No module named pytest`

Use the project virtual environment:

```bash
cd backend
source .venv/bin/activate
python -m pytest tests -q
```

### `ModuleNotFoundError` for spaCy model

```bash
cd backend
source .venv/bin/activate
python -m spacy download en_core_web_sm
```

### Connection refused / database not reachable

Check that Docker is running and the DB is healthy:

```bash
docker ps
docker logs resume_screener_db
```

Then confirm your `DATABASE_URL` matches the container port:

```text
postgresql://admin:random_password@localhost:5433/resume_screener
```

## Quick start summary

```bash
cd smart-resume-screener
docker compose up -d db
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

Then open:

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
