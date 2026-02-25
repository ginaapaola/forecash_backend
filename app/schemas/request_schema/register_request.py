from typing import List

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):

    #DATOS DEL REPRESENTANTE
    rep_name: str
    rep_email: EmailStr
    rep_phone: str
    rep_document_type: str 
    rep_document_number: str = Field(min_length=8, max_length=10)

    #DATOS DE LA EMPRESA
    legal_name_company: str
    trade_name_company: str
    nit_company: str
    economic_activity: str
    entity_type: str
    is_legally_constituted: bool

class AditionalUser(BaseModel):
    name: str
    email: EmailStr
    document_type: str
    document_number: str = Field(min_length=8, max_length=10)


class CompanyRequestCreate(RegisterRequest):
    aditional_user: List[AditionalUser] = []
