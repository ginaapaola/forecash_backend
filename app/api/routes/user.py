from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_rol import require_role
from app.dependencies.require_super_admin import require_super_admin
from app.models.user.user import User
from app.models.user_company.company_role import CompanyRole
from app.schemas.request_schema.auth_request import ChangePasswordRequest
from app.schemas.request_schema.user_request import CreateUserRequest, UserRequestUpdate
from app.schemas.response_schema.http_responses import ForbiddenResponse, NotFoundResponse, UnauthorizedResponse
from app.schemas.response_schema.user_response import UserResponse
from app.services.users.users_services import UsersService



router = APIRouter(prefix="/users", tags=['Users'])

@router.get(
        "/user", 
        response_model=UserResponse,
        responses={
            404: {"model": NotFoundResponse},
            403: {"model": ForbiddenResponse},
            401: {"model": UnauthorizedResponse}
        }
        )
def get_user_by_id(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return UsersService.get_user(db, current_user.id )

@router.get(
    "/",
    response_model=List[UserResponse],
    description="Endpoint to get all users",
    responses={
        404: {"model": NotFoundResponse},
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def get_users(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
): 
    return UsersService.get_all_users(db)

@router.put(
    "/{user_id}/change-password",
    description="Endpoint to change password",
    responses={
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    return UsersService.update_user_password(db, current_user.id, data)

@router.put(
    "/{user_id}/update",
    description="Endpoint to Update User",
    responses={
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def update_user(
    data:UserRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return UsersService.update_user(db, current_user.id, data)

@router.patch(
    "/deactivated/{user_id}",
    description= "Endpoint to deactivated an User",
    responses={
        403: {"model": ForbiddenResponse},
        401: {"model": UnauthorizedResponse}
    }
)
def deactivated_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    return UsersService.deactivate_user(db, user_id)