'''
export TEST_DATABASE_URL="$(grep '^DATABASE_URL=' .env | cut -d= -f2- | sed 's#/resume_screener$#/resume_screener_test#')"
python -m eval.evidence
'''


from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import settings
from app.routers import auth, jobs, resumes, scoring, resume_batch
from app.database import get_db


app = FastAPI(title=settings.APP_NAME)

origins = [
	"http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods=["*"],   # allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(scoring.router)
app.include_router(resume_batch.router)


# @app.get("/")
# def read_root():
#     return {
#         "message": f"{settings.APP_NAME} API is alive",
#         "debug_mode": settings.DEBUG,
#     }

@app.get("/")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return {"status": "degraded", "database": "disconnected"}
