from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.dependencies.get_rol import require_role
from app.models.user.user import User
from app.models.user_company.company_role import CompanyRole
from app.schemas.request_schema.user_request import CreateUserRequest
from app.schemas.response_schema.http_responses import ForbiddenResponse, UnauthorizedResponse
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