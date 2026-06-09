"""Endpoints para solicitudes de registro de empresas.

Permite crear solicitudes con archivos de soporte y administrarlas desde el rol
super administrador hasta su aprobacion o rechazo.
"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.dependencies.require_super_admin import require_super_admin
from app.models.user.user import User
from app.schemas.request_schema.register_request import RegisterRequestUpdate
from app.schemas.response_schema.http_responses import ForbiddenResponse, NotFoundResponse, UnauthorizedResponse
from app.schemas.response_schema.register_response import RegisterResponse
from app.services.requests.requests_services import RequestsServices

router = APIRouter(prefix="/requests", tags=["Requests"])

#ENDPOINT PARA LA CREACIÓN DE UNA NUEVA SOLICITUD DE REGISTRO
@router.post(
    ("/"),
    response_model=RegisterResponse
)
def create_register_request(
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
    """Crea una solicitud de registro de empresa con datos y adjuntos."""
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

#ENDPOINT PARA OBTENER UNA SOLICITUD POR SU ID
@router.get(
    "/{request_id}",
    response_model=RegisterResponse,
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def get_request(
    request_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Obtiene una solicitud de registro por ID."""
    return RequestsServices.get_request_id(db, request_id)

#ENDPOINT PARA OBTENER UNA LISTA DE SOLICITUDES
@router.get(
    "/",
    response_model=List[RegisterResponse],
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def get_requests(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Lista solicitudes de registro ordenadas por fecha de creacion."""
    return RequestsServices.get_all_requests(db)

@router.put(
    "/reject/{request_id}",
    description="Endpoint to reject request",
    response_model=RegisterResponse,
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def reject_request(
    request_id: int,
    data: RegisterRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Rechaza una solicitud de registro y conserva el motivo."""
    return RequestsServices.reject_request(db, request_id, data)

@router.put(
    "/approved/{request_id}",
    description="Endpoint to approve request",
    response_model=RegisterResponse,
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def approve_request(
    request_id: int,
    background_task: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """Aprueba una solicitud y crea empresa, usuarios y tareas de email."""
    return RequestsServices.approved_request(db, request_id, background_task)
