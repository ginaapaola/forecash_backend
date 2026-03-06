from typing import List

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
    users: List[UserBasicResponse] = []

    class Config:
        from_attributes = True
    