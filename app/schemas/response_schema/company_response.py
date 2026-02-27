from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id: int
    legal_name: str
    trade_name: str
    nit: str
    economic_sector: str
    economic_activity: str
    entity_type: str
    is_legally_constituted: bool
    