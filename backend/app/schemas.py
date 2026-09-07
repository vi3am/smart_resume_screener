from pydantic import BaseModel, EmailStr
from datetime import datetime


class EchoRequest(BaseModel):
    name: str
    message: str
    

class EchoResponse(BaseModel):
    reply: str
    

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True