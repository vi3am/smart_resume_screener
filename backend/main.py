from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas import EchoRequest, EchoResponse
from app.routers import practice

app = FastAPI(title=settings.app_name)

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

app.include_router(practice.router)

@app.get("/")
def read_root():
	return {
        "message": f"{settings.app_name} API is alive", 
        "debug_mode": settings.debug
    }

