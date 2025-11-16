from pydantic import BaseModel, EmailStr, Field, field_validator
from app.utils.validators import validate_cpf


class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    cpf: str = Field(..., min_length=11, max_length=14)
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator("cpf")
    @classmethod
    def validate_cpf_field(cls, v: str) -> str:
        if not validate_cpf(v):
            raise ValueError("Invalid CPF format or checksum")
        return v.replace(".", "").replace("-", "")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

