from pydantic import BaseModel

from app.schemas.response_schema.company_response import CompanyResponse


class UserCompanyResponse(BaseModel):
    role: str
    company: CompanyResponse

    class Config:
        from_attributes = True

