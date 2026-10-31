# Smart Resume Screener

A full-stack app for creating job postings, uploading resumes, and matching candidates to a job description. The backend is FastAPI with PostgreSQL; the frontend is React and Vite.

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
