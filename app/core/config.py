from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = "SECRET-KEY"
    JWT_ALGORITH: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

settings = Settings()