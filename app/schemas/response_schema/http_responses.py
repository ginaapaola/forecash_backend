from pydantic import BaseModel


class NotFoundResponse(BaseModel):
    message: str = "Not found"

class ForbiddenResponse(BaseModel):
    message: str = "You're not authenticated"

class UnauthorizedResponse(BaseModel):
    message: str = "You're not authorized for this action"