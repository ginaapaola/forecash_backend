from typing import List

from pydantic import BaseModel

from app.schemas.response_schema.company_response import CompanyResponse



class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: str
    document_type: str
    document_number: str
    companies: List[CompanyResponse]