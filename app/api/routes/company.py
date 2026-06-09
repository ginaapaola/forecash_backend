"""Endpoints de empresas, dashboard y metricas.

Centraliza operaciones sobre empresas: seleccion, consulta, configuracion
tributaria, usuarios asociados, datasets y metricas del tablero financiero.
"""

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import String
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.dependencies.get_company import get_company
from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_rol import require_role
from app.dependencies.require_super_admin import require_super_admin
from app.models.dimensions.operation_type import OperationType
from app.models.user.user import User
from app.models.user_company.company_role import CompanyRole
from app.schemas.request_schema.select_company import SelectCompanyRequest
from app.schemas.request_schema.tax_configuration import TaxConfiguration
from app.schemas.request_schema.user_request import CreateUserRequest
from app.schemas.response_schema.company_response import CompanyResponse
from app.schemas.response_schema.dataset_response import DatasetListResponse
from app.schemas.response_schema.http_responses import ForbiddenResponse, NotFoundResponse, UnauthorizedResponse
from app.schemas.response_schema.select_company_response import CompanySelectedResponse
from app.services.company.company_service import CompanyService
from app.services.datasets.calculate_metrics import calculate_metrics_by_period, get_categories_breakdown, get_expense_evolution, get_operation_breakdown, get_product_evolution, get_products_record
from app.services.users.users_services import UsersService


router = APIRouter(prefix="/company", tags=['Company'])

@router.post(
    "/{company_id}/user",
    description="Endpoint to add new user in company",
    responses={
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def post_user_company(
    company_id: int,
    data: CreateUserRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(CompanyRole.LEGAL_REPRESENTATIVE))
):
    """Crea o asocia un usuario dentro de una empresa existente."""
    return UsersService.create_user_for_company(db, company_id, data, user.id)

@router.post(
        "/select-company",
        response_model=CompanySelectedResponse
)
def select_company(
    data: SelectCompanyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Selecciona una empresa del usuario y devuelve su rol en ella."""
    return CompanyService.select_company(db, data, user.id)


@router.get(
    "/",
    response_model=List[CompanyResponse],
    description="Endpoint to get all companies",
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def get_companies(
    db:Session = Depends(get_db),
    user: User = Depends(require_super_admin)
): 
    """Lista todas las empresas registradas para administradores."""
    return CompanyService.get_companies(db)


@router.get("/metrics")
def get_metrics_by_period(
    fecha_inicio: date,
    fecha_fin: date,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)
):
    """Calcula KPIs y series del dashboard para un rango de fechas."""
    company_id = company["company"].id
    return calculate_metrics_by_period(
        db, company_id, fecha_inicio, fecha_fin
    )

@router.get("/dashboard/breakdown")
def get_breakdown(
    operation_type: OperationType,
    start: date,
    end: date,
    company: dict = Depends(get_company),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Obtiene la distribucion de una operacion financiera por periodo."""
    company_id = company["company"].id
    return get_operation_breakdown(
        db,
        company_id,
        operation_type,
        start,
        end,
    )

@router.get("/dashboard/categories/products")
def get_products_by_categories(
    start: date,
    end: date,
    category_id: int,
    company: dict = Depends(get_company),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Lista productos vendidos dentro de una categoria y rango de fechas."""
    company_id = company["company"].id
    return get_categories_breakdown(
        db,
        company_id,
        category_id,
        start,
        end
    )

@router.get("/dashboard/categories/products/product")
def get_product_payload_category(
    start:date, 
    end: date,
    product_id: int,
    company: dict = Depends(get_company),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Devuelve registros crudos asociados a un producto vendido."""
    company_id = company["company"].id
    return get_products_record(
        db,
        company_id,
        product_id,
        start,
        end
    )

@router.get("/dashboard/products/product")
def get_evolution_product(
    product: int,
    start: date,
    end: date,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)   
): 
    """Calcula la evolucion historica de ventas, compras y utilidad de un producto."""
    company_id = company["company"].id
    return get_product_evolution(db, company_id, product, start, end)

@router.get("/dashboard/expenses/evolution")
def expense_evolution(
    expense: str,
    start: date,
    end: date,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)   

):
    """Calcula la evolucion de un gasto especifico en un periodo."""
    company_id = company["company"].id
    return get_expense_evolution(
        db=db,
        company_id=company_id,
        expense_name=expense,
        fecha_inicio=start,
        fecha_fin=end,
    )

@router.get(
        "/datasets",
        description="Endpoint to get company's datasets",
        response_model=List[DatasetListResponse]
)
def get_datasets_by_company(
    company: dict = Depends(get_company),
    db: Session = Depends(get_db)
):
    """Lista datasets cargados para la empresa activa."""
    company_id = company["company"].id
    return CompanyService.get_datasets(db, company_id)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    description="Endpoint to get company's info",
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def get_company_id(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Consulta informacion detallada de una empresa por ID."""
    return CompanyService.get_company_id(db, company_id)

@router.patch(
    "/{company_id}/tax-config",
    response_model=CompanyResponse,
    description= "Endpoint to update tax information",
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def update_tax_config(
    data: TaxConfiguration,
    company_data: dict = Depends(get_company),
    db: Session = Depends(get_db)
):
    """Actualiza la configuracion tributaria de la empresa activa."""
    return CompanyService.update_tax_config(db, company_data, data)

@router.delete(
    "/datasets/{dataset_id}",
    description="Endpoint to delete a company's dataset",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_dataset(
    dataset_id: int,
    company: dict = Depends(get_company),
    db: Session = Depends(get_db)
):
    """Elimina un dataset de la empresa activa."""
    company_id = company["company"].id
    CompanyService.delete_dataset(db, company_id, dataset_id)
