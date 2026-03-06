# user_basic_response.py
from pydantic import BaseModel

class UserBasicResponse(BaseModel):
    id: int
    name: str
    email: str
    document_number: str

    class Config:
        from_attributes = True