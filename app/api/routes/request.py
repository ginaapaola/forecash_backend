from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile

from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.schemas.response_schema.register_response import RegisterResponse
from app.services.requests.requests_services import RequestsServices

router = APIRouter(prefix="/requests", tags=["Requests"])

@router.post(
    ("/"),
    response_model=RegisterResponse
)
def createRequest(
    rep_name: str = Form(...),
    rep_email: str = Form(...),
    rep_phone: str = Form(...),
    rep_document_type: str = Form(...),
    rep_document_number: str = Form(...),
    legal_name_company: str = Form(...),
    trade_name_company: str = Form(...),
    nit_company: str = Form(...),
    economic_activity: str = Form(...),
    entity_type: str = Form(...),
    is_legally_constituted: bool = Form(...),
    usuarios_json: str = Form("[]"),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    data = {
        "rep_name": rep_name,
        "rep_email": rep_email,
        "rep_phone": rep_phone,
        "rep_document_type": rep_document_type,
        "rep_document_number": rep_document_number,
        "legal_name_company": legal_name_company,
        "trade_name_company": trade_name_company,
        "nit_company": nit_company,
        "economic_activity": economic_activity,
        "entity_type": entity_type,
        "is_legally_constituted": is_legally_constituted,
        "usuarios_json": usuarios_json
    }
    return RequestsServices.create_request(
        db=db,
        data=data,
        files=files
    )