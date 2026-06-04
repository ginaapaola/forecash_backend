"""Endpoints para carga y procesamiento de datasets.

Recibe archivos CSV/XLSX asociados a la empresa seleccionada y delega la
validacion, persistencia y ETL al servicio de datasets.
"""

from fastapi import APIRouter, Depends, File, UploadFile

from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.dependencies.get_company import get_company
from app.dependencies.get_current_user import get_current_user
from app.models.user.user import User
from app.services.datasets.dataset_services import DatasetService


router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)

):
    """Procesa un archivo subido para la empresa activa del usuario."""
    company_id = company["company"].id
    return await DatasetService.process_file(file, db, company_id, user.id)
