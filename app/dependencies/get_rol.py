from fastapi import Depends, HTTPException

from app.dependencies.get_current_user import get_current_user


def role_required(required_role: str):

    def role_dependency(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != required_role:
           raise HTTPException(
             status_code=403 ,
             detail = "You're not authorization for this action"
           )
        return current_user
    
    return role_dependency