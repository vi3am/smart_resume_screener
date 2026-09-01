from fastapi import APIRouter
from app.schemas import EchoResponse, EchoRequest

router = APIRouter(prefix="/practice", tags=["practice"])

@router.post("/echo", response_model=EchoResponse)
def echo(payload: EchoRequest):
    return EchoResponse(reply=f"Hey {payload.name}, you said: {payload.message}")