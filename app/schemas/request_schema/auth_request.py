from pydantic import BaseModel


class LoginRequest(BaseModel):
    usuario: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str