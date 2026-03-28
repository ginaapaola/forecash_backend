from datetime import date
from typing import List

from fastapi import APIRouter, Depends, status
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
from app.services.datasets.calculate_metrics import calculate_metrics_by_period, get_operation_breakdown
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
    return CompanyService.get_companies(db)


@router.get("/metrics")
def get_metrics_by_period(
    fecha_inicio: date,
    fecha_fin: date,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company),
    user: User = Depends(get_current_user)
):
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
    company_id = company["company"].id
    return get_operation_breakdown(
        db,
        company_id,
        operation_type,
        start,
        end,
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
    company_id = company["company"].id
    CompanyService.delete_dataset(db, company_id, dataset_id)