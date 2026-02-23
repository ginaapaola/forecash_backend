from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db.session import get_db
from app.dependencies.get_current_user import get_current_user
from app.models.user.user import User

def get_current_user_from_db(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = payload.get("sub")

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    return user