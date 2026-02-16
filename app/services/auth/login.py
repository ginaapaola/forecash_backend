from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from app.core.db.session import get_db
from app.core.security import create_access_token, create_refresh_token, hash_token, verify_password
from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user.user import User
from app.schemas.auth import LoginRequest
from sqlalchemy.orm import Session


async def login(
        data: LoginRequest,
        db: Session = Depends(get_db)
):
    #Buscar y validar que el usuario sí existe en la BD
    user = db.query(User).filter(User.email == data.email).first()

    if not user: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid credentials"
        )
    
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid credentials"
        )
    
    #crear token
    access_token = create_access_token(
        user_id = user.id,
        role = user.role
    )
    
    refresh_token = create_refresh_token(user.id)

    expires_at = datetime.utcnow() + timedelta(
        days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    save_refresh_token = RefreshToken(
        user_id = user.id,
        token_hash = hash_token(refresh_token),
        expires_at = expires_at,
        revoked = False
    )

    db.add(save_refresh_token)
    try:
        db.commit()
    except Exception as e:
        print("ERROR: ", e)
        db.rollback()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }