from typing import List, Optional

from pydantic import BaseModel

from app.schemas.response_schema.user_basic_response import UserBasicResponse



class CompanyResponse(BaseModel):
    id: int
    legal_name: str
    trade_name: str
    nit: str
    economic_sector: str
    economic_activity: str
    entity_type: str
    is_legally_constituted: bool
    regime_type: Optional[str] = None
    tax_rate: Optional[float] = None
    is_vat_responsible: Optional[bool] = None
    users: List[UserBasicResponse] = []

    class Config:
        from_attributes = True
    