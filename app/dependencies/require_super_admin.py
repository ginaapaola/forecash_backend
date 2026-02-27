from fastapi import Depends, HTTPException

from app.dependencies.get_current_user import get_current_user
from app.models.user.user import User
from app.models.user.user_role import UserRole

def require_super_admin(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Solo super admin puede realizar esta acción"
        )
    return current_user