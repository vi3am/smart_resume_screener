# Smart Resume Screener

An AI-powered job matching app that lets recruiters create job posts, upload resumes, and get ranked candidate matches based on resume-to-job similarity.

## Technologies

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL
- Auth: JWT
- Resume parsing: pdfplumber, python-docx, spaCy
- Matching: sentence-transformers
- Containerization: Docker Compose

## Prerequisites

Make sure these are installed:

- Python 3.11+
- Node.js 18+
- npm
- Docker Desktop or Docker Engine
- Git

Check versions:

```bash
python3 --version
node --version
npm --version
docker --version
git --version
```

## 1) Clone the project

```bash
git clone https://github.com/vi3am/smart_resume_screener.git
cd smart_resume_screener
```

## 2) Configure backend environment

Create a file named `.env` inside `backend/`:

```bash
cd backend
cat > .env <<'EOF'
APP_NAME=Smart Resume Screener
DEBUG=True
JWT_SECRET_KEY=change-me-to-a-long-random-string
DATABASE_URL=postgresql://admin:random_passowrd@localhost:5432/resume_screener
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
POSTGRES_USER=admin
POSTGRES_PASSWORD=random_passowrd
POSTGRES_DB=resume_screener
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
EOF
```

Important:
- The app reads environment variables from `backend/.env`.
- Docker Compose also uses that file through `docker-compose.yml`.
- If you change the Postgres password, recreate the database volume.

## 3) Start PostgreSQL with Docker

From the project root:

```bash
docker compose up -d db
```

Check the container:

```bash
docker ps
```

You should see a Postgres container running on port `5432`.

## 4) Install Python dependencies

Create and activate a virtual environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

Install packages:

```bash
pip install -r requirements.txt
```

If spaCy models are not already installed, download the English model:

```bash
python -m spacy download en_core_web_sm
```

## 5) Run database migrations

From the backend directory:

```bash
alembic upgrade head
```

## 6) Run the backend

From the backend directory:

```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Optional health check:

```bash
curl http://localhost:8000/docs
```

## 7) Install and run the frontend

Open a second terminal and run:

```bash
cd frontend
npm install
npm run dev
```

Then open:

- http://localhost:5173

The frontend expects the API at `http://localhost:8000`.

## 8) Run the backend tests

From the backend directory:

```bash
source .venv/bin/activate
python -m pytest tests -q
```

## 9) Useful commands

### Start database only

```bash
docker compose up -d db
```

### Start backend only

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

### Start frontend only

```bash
cd frontend
npm run dev
```

### Reset database

```bash
docker compose down -v
docker compose up -d db
cd backend
alembic upgrade head
```

## Common issues

### `password authentication failed for user "admin"`

You changed the Postgres password in `backend/.env` but the database volume was already created.

Reset the database:

```bash
docker compose down -v
docker compose up -d db
cd backend
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

Install the model:

```bash
cd backend
source .venv/bin/activate
python -m spacy download en_core_web_sm
```

## Project structure

```text
smart-resume-screener/
├── backend/
│   ├── .env
│   ├── .venv/
│   ├── alembic/
│   ├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── tests/
│   └── uploads/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── README.md
└── smart-resume-screener.code-workspace
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

Then in another terminal:

```bash
cd frontend
npm install
npm run dev
```
