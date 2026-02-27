from typing import Optional

from pydantic import BaseModel, Field


class UserRequestUpdate(BaseModel):
    phone: Optional[str] = Field(None, min_length=6)