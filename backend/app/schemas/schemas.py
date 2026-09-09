from pydantic import BaseModel, EmailStr
from datetime import datetime


class EchoRequest(BaseModel):
    name: str
    message: str
    

class EchoResponse(BaseModel):
    reply: str
    

