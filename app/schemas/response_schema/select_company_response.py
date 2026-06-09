from pydantic import BaseModel


class CompanySelectedResponse(BaseModel):
    company_id: int
    role: str