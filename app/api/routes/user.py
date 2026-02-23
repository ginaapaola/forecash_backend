from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.dependencies.get_user import get_current_user_from_db
from app.models.user.user import User
from app.schemas.user_response import ForbiddenResponse, NotFoundResponse, UnauthorizedResponse, UserResponse
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
def getUser(
    current_user: User = Depends(get_current_user_from_db),
    db: Session = Depends(get_db)
):
    return UsersService.get_user(db, current_user.id )
