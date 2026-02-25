from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.request.register_request import RegisterRequest
from app.schemas.request_schema.register_request import AditionalUser

class RequestFileResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class RegisterResponse(RegisterRequest):
    id: int
    state: str
    motivo_rechazo: Optional[str]
    created_at: datetime

    aditional_users: Optional[list[AditionalUser]] = []
    files: list[RequestFileResponse] = []

    class Config:
        from_attributes = True