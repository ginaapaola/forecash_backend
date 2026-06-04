"""Endpoints de autenticacion.

Expone inicio de sesion, renovacion de tokens y consulta del perfil codificado
en el token JWT actual.
"""

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.dependencies.get_token_payload import get_token_payload
from app.core.db.session import get_db

from app.schemas.request_schema.auth_request import LoginRequest, RefreshRequest
from app.schemas.response_schema.auth import TokenResponse
from app.services.auth.login import login
from app.services.auth.refresh_token import refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# REFRESH TOKENS
@router.post("/refresh", response_model=TokenResponse)
async def token(
    token_req: RefreshRequest,
    db: Session = Depends(get_db)
):
    """Renueva el access token a partir de un refresh token valido."""
    return await refresh_token(token_req, db)

# LOGUEO 
@router.post(
        "/login", 
        responses= {
            400: {"BAD REQUEST": "Invalid credentials"}
        }
        )
async def authenticate_user(
    login_request: LoginRequest = Body(
        ...,
        examples=[
            {
                "usuario": "username",
                "password": "userpassword"
            }
        ]
    ),
    db: Session = Depends(get_db)
): 
    """Autentica credenciales y entrega tokens de acceso y refresco."""
    return await login(login_request, db)

@router.get("/profile")
def get_profile(current_user: dict = Depends(get_token_payload)):
    """Devuelve el payload del token autenticado."""
    return current_user
