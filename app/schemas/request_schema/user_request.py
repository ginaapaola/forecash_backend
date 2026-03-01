from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user_company.company_role import CompanyRole

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    role: str = Field(default=CompanyRole.USER)
    phone: str
    document_type: str
    document_number: str

class UserRequestUpdate(BaseModel):
    phone: Optional[str] = Field(None, min_length=6)