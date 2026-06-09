"""Dependencia para resolver el usuario autenticado actual."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.dependencies.get_token_payload import get_token_payload
from app.models.user.user import User

def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db)
):
    """Obtiene el usuario de base de datos indicado por el token JWT."""
    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    return user
