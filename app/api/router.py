from fastapi import APIRouter, Depends
from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_rol import role_required

from app.api.routes.auth import router as auth_router
from app.api.routes.user import router as users_router
from app.api.routes.request import router as request_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(request_router)


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Forecash is runing"}


"""
@router.get("/admin/dashboard")
def admin_dashboard(
    current_user: dict = Depends(role_required("super_admin"))
):
    return {"message": "panel de admin"}
"""
