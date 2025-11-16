from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    cpf: str
    created_at: datetime
    updated_at: datetime

