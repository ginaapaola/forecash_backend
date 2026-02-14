from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status
import hashlib
from app.core.config import settings



pwd_context = CryptContext(
    #Protección contra ataques de fuerza bruta 
    schemes=["bcrypt"],
    #manejo de hashes viejos (por si hay un cambio de algoritmo en el futuro)
    deprecated="auto"
)

#Hasheo de contraseñas, nunca se guardan en texto plano
def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])


#Verificación de contraseñas 
def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(user_id: int, role: str):
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

def create_refresh_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def decode_refresh_token(token: str) -> dict:
    try: 
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
