from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings


pwd_context = CryptContext(
    #Protección contra ataques de fuerza bruta 
    schemes=["bcrypt"],
    #manejo de hashes viejos (por si hay un cambio de algoritmo en el futuro)
    deprecated="auto"
)

#Hasheo de contraseñas, nunca se guardan en texto plano
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


#Verificación de contraseñas 
def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datatime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    
    #Firma del token, así se evitan modificaciones
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITH
    )