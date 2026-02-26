from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.request_schema.register_request import AditionalUser, RegisterRequest

class RequestFileResponse(BaseModel):
    id: int
    file_name: str
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class RegisterResponse(RegisterRequest):
    id: int
    status: str
    reason_for_rejection: Optional[str]
    created_at: datetime

    aditional_users: Optional[list[AditionalUser]] = []
    files: list[RequestFileResponse] = []

    class Config:
        from_attributes = True
