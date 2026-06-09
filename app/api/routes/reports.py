"""Endpoints para generacion y descarga de reportes PDF."""

from datetime import date

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session 

from app.core.db.session import get_db
from app.dependencies.get_company import get_company
from app.dependencies.get_current_user import get_current_user
from app.models.user.user import User
from app.services.reports.reports_service import generar_reporte_pdf, generar_reporte_producto_pdf, generar_reporte_productos


router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/pdf")
def descargar_reporte(
    fecha_inicio: date,
    fecha_fin: date,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)
):
    """Genera un reporte financiero general en PDF para la empresa activa."""
    company_id = company["company"].id
    company_name = company["company"].legal_name
    pdf = generar_reporte_pdf(
        db=db,
        empresa=company_name,
        usuario=user.name,
        company_id=company_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_{company_name}.pdf"}
    )

@router.get("/products/pdf")
def descargar_reporte_productos(
    fecha_inicio: date,
    fecha_fin: date,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)
):
    """Genera un reporte PDF con resumen de productos del periodo."""
    company_id = company["company"].id
    company_name = company["company"].legal_name
    pdf = generar_reporte_productos(
        db=db,
        empresa=company_name,
        usuario=user.name,
        company_id=company_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_productos_{company_name}.pdf"}
    )

@router.get("/evolution/product/pdf")
def descargar_reporte_evolucion_producto(
    fecha_inicio: date,
    fecha_fin: date,
    product_id: int,
    nombre_producto: str,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)
):
    """Genera un reporte PDF de evolucion para un producto especifico."""
    company_id = company["company"].id
    company_name = company["company"].legal_name
    pdf = generar_reporte_producto_pdf(
        db=db,
        empresa=company_name,
        usuario=user.name,
        company_id=company_id,
        product_id=product_id,
        nombre_producto=nombre_producto,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_{nombre_producto}.pdf"}
    )
