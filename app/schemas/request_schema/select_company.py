from pydantic import BaseModel


class SelectCompanyRequest(BaseModel):
    company_id: int