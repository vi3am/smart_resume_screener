from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import practice, auth, jobs, resumes

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

@app.get("/")
def read_root():
    return {
        "message": f"{settings.APP_NAME} API is alive",
        "debug_mode": settings.DEBUG,
    }

