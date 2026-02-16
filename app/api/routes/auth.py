from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.auth import RefreshRequest, TokenResponse, LoginRequest
from app.core.db.session import get_db
from app.services.auth.login import login
from app.services.auth.refresh_token import refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# REFRESH TOKENS
@router.post("/refresh", response_model=TokenResponse)
async def token(
    token_req: RefreshRequest,
    db: Session = Depends(get_db)
):
    return await refresh_token(token_req, db)

# LOGUEO 
@router.post(
        "/login", 
        response_model=TokenResponse,
        responses= {
            404: {"Error": "Not found"}
        }
        )
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