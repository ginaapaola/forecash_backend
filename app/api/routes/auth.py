from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.schemas.auth import RefreshRequest, TokenResponse, LoginRequest
from app.models.refresh_token import RefreshToken
from app.models.user.user import User
from app.core.security import (
    decode_refresh_token,
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_password
)
from app.core.config import settings
from app.core.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# VALIDACIÓN DE REFRESH TOKEN, REVOCACIÓN Y CREACIÓN DE NUEVOS TOKENS

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_db)
):
    #Validar refresh token (firma + exp)
    payload = decode_refresh_token(data.refresh_token)
    user_id = int(payload["sub"])

    #Buscar el token en la base de datos
    token_hash = hash_token(data.refresh_token)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not valid"
        )

    #Obtener el usuario (para el role)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    #Rotar refresh token (revocar el actual)
    db_token.revoked = True

    # Crear nuevos tokens
    new_access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )

    new_refresh_token = create_refresh_token(user.id)

    # Guardar el nuevo refresh token
    expires_at = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    new_db_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh_token),
        expires_at=expires_at,
        revoked=False
    )

    db.add(new_db_token)
    db.commit()

    #Responder
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }

# LOGUEO 

@router.post(
        "/login",
        response_model=TokenResponse,
        )
async def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    #Buscar usuario
    user = db.query(User).filter(User.email == data.email).first()

    if not user: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials"
        )
    
    #Verificar contraseña
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    #crear token
    access_token = create_access_token(
        user_id= user.id,
        role = user.role
    )

    refresh_token = create_refresh_token(user.id)

    #Guardar el refresh toen en la BD 

    expires_at = datetime.utcnow() + timedelta(
        days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    db_refresh_token = RefreshToken(
        user_id = user.id,
        token_hash = hash_token(refresh_token),
        expires_at = expires_at,
        revoked = False
    )

    db.add(db_refresh_token)
    try:
        db.commit()
    except Exception as e:
        print("ERROR: ", e)
        db.rollback()

    print("LOGUEO EXITOSO, TOKENS CREADOS: ", access_token)

    return{
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }