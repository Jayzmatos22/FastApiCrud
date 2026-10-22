from pydantic import BaseModel, EmailStr, Field, Configdict, field_validator
from datetime import datetime


class CreateUser(BaseModel):
    name: str = Field(min_length=3, max_length=50,
    description="Nome com 3 a 50 caracteres")
    email: EmailStr
    password: 

    @field_validator("email")
    @classmethod
    def valid_email(cls, e: str) -> str:
        if "@" not in e:
            raise ValueError("E-mail inválido. Deve conter '@'")
        return e

    
    @field_validator("name")
    @classmethod
    def limpar_nome(cls, n: str) -> str:
        if len(n.split()) < 2:
            raise ValueError("Formato inválido. Deve ser [Nome Sobrenome]")

        if any(d.isdigit() for d in n):
            raise ValueError("Nome não pode ter número")

        return n  


class ResponseUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: datetime