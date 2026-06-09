"""Utilidades de seguridad y tokens.

Centraliza hashing de contrasenas, verificacion de credenciales, generacion de
JWT de acceso/refresco/activacion y hashing de refresh tokens.
"""

import secrets
import string

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
    """Genera un hash bcrypt para almacenar una contrasena."""
    return pwd_context.hash(password[:72])


#Verificación de contraseñas 
def verify_password(password: str, hashed: str) -> bool:
    """Verifica una contrasena en texto plano contra su hash."""
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict):
    """Crea un JWT de acceso con expiracion corta."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        settings.JWT_ALGORITHM
    )

def create_refresh_token(user_id: int):
    """Crea un JWT de refresco asociado a un usuario."""
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
    """Genera un hash SHA-256 para almacenar tokens opacos."""
    return hashlib.sha256(token.encode()).hexdigest()

def decode_refresh_token(token: str) -> dict:
    """Decodifica y valida un refresh token JWT."""
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

# FUNCIÓN PARA GENERAR UNA CONTRASEÑA SEGURA
def generate_secure_pass(length: int = 8) -> str:
    """Genera una contrasena temporal con letras, numeros y simbolos."""

    alphabet = string.ascii_letters + string.digits + "!@#$%&*"

     # Garantizar al menos un carácter de cada tipo
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*"),
    ]

    # Completar el resto
    password += [secrets.choice(alphabet) for _ in range(length - 4)]

    secrets.SystemRandom().shuffle(password)

    return "".join(password)

# FUNCIÓN PARA GENERAR TOKENS DE ACTIVACIÓN DE CUENTA (Expira en 3 dias || 72 horas)

def create_activation_token(user_id: int) -> str:
    """Crea un JWT de activacion de cuenta con vigencia de 72 horas."""
    
    payload = {
        "sub": str(user_id),
        "type": "activation",
        "exp": datetime.utcnow() + timedelta(hours=72),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
