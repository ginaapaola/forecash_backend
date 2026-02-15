from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from app.api.routes.auth import refresh_token, login
from app.core.db.session import get_db
from app.dependencies.get_current_user import get_current_user
from app.dependencies.get_rol import role_required
from app.schemas.auth import TokenResponse, LoginRequest, RefreshRequest

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Forecash is runing"}

@router.post("/refreshToken", response_model=TokenResponse)
async def token(
    token_req: RefreshRequest,
    db: Session = Depends(get_db)
):
    return await refresh_token(token_req, db)

@router.post("/login", response_model=TokenResponse)
async def authenticate_user(
    login_request: LoginRequest = Body(
        ...,
        examples=[
            {
                "email": "user@gmail.com",
                "password": "userpassword"
            }
        ]
    ),
    db: Session = Depends(get_db)
): 
    return await login(login_request, db)

@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@router.get("/admin/dashboard")
def admin_dashboard(
    current_user: dict = Depends(role_required("super_admin"))
):
    return {"message": "panel de admin"}
