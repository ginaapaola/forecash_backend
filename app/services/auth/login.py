from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_password
)
from app.core.config import settings

from app.models.refresh_token import RefreshToken
from app.models.user.user import User
from app.models.user.user_role import UserRole

from app.schemas.request_schema.auth_request import LoginRequest


async def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):

    # Buscar usuario
    user = db.query(User).filter(
        User.document_number == data.usuario
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verificar contraseña
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Crear access token (solo identidad)
    access_token = create_access_token(
        {
            "sub": str(user.id),
            "is_superadmin": user.role == UserRole.SUPER_ADMIN
        }
    )

    # Crear refresh token
    refresh_token = create_refresh_token(user.id)

    expires_at = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    # Guardar refresh token en BD
    save_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        revoked=False
    )

    db.add(save_refresh_token)

    try:
        db.commit()
    except Exception as e:
        print("ERROR:", e)
        db.rollback()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }