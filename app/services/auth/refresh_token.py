from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from app.core.db.session import get_db
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, hash_token
from app.models.refresh_token import RefreshToken
from app.models.user.user import User
from app.schemas.auth import RefreshRequest
from sqlalchemy.orm import Session
from app.core.config import settings


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
