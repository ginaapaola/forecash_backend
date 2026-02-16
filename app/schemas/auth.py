from pydantic import BaseModel

class LoginRequest(BaseModel):
    usuario: str
    password: str
        

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str