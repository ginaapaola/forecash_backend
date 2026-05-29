from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    #enviroment
    ENV: str = "development"
    DEBUG: bool = False

    #security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

    #Database
    DB_URL: str
    # DB_HOST: str
    # DB_PORT: int = 5432
    # DB_NAME: str
    # DB_USER: str
    # DB_PASSWORD: str

    #SUPERADMIN
    SUPERADMIN_NAME: str
    SUPERADMIN_EMAIL: str
    SUPERADMIN_PASS: str
    SUPERADMIN_PHONE: str
    SUPERADMIN_DOC_TYPE: str
    SUPERADMIN_DOC_NUM: str

    #FIREBASE
    FIREBASE_CREDENTIALS_PATH: str
    FIREBASE_STORAGE_BUCKET: str

    #VARIABLES EMAIL
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    

    @property
    def DATABASE_URL(self) -> str:
        return self.DB_URL
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()