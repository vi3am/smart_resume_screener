from pydantic import BaseModel


class EchoRequest(BaseModel):
    name: str
    message: str
    

class EchoResponse(BaseModel):
    reply: str