from typing import List, Optional

from pydantic import BaseModel

from app.schemas.response_schema.UserCompanyResponse import UserCompanyResponse



class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: Optional[str] = None
    phone: Optional[str]
    document_type: str
    document_number: str
    companies: List[UserCompanyResponse] = []

    class Config:
        from_attributes = True