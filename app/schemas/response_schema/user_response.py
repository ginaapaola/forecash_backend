from typing import List

from pydantic import BaseModel, ConfigDict

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

    class Config:
        from_attributes = True