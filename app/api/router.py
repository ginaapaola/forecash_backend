from fastapi import APIRouter, Depends
from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_rol import role_required

from app.api.routes.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router)


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Forecash is runing"}

"""    
@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/admin/dashboard")
def admin_dashboard(
    current_user: dict = Depends(role_required("super_admin"))
):
    return {"message": "panel de admin"}
"""
