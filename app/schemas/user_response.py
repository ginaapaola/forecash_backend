from typing import List

from pydantic import BaseModel

from app.schemas.company_response import CompanyResponse


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: str
    document_type: str
    document_number: str
    companies: List[CompanyResponse]

class NotFoundResponse(BaseModel):
    message: str = "User hasn't been found"

class ForbiddenResponse(BaseModel):
    message: str = "You're not authenticated"

class UnauthorizedResponse(BaseModel):
    message: str = "You're not authorized for this action"