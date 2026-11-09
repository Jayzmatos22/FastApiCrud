from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field


def validar_nome(n: str) -> str:
    n = n.strip()

    if len(n.split()) < 2:
        raise ValueError("Formato inválido. Deve ser [Nome Sobrenome]")

    if any(d.isdigit() for d in n):
        raise ValueError("Nome não pode ter número")

    return n


Nome = Annotated[
    str,
    Field(min_length=3, max_length=50, description="Nome com 3 a 50 caracteres"),
    AfterValidator(validar_nome),
]


class CreateUser(BaseModel):
    name: Nome
    email: EmailStr
    password: str = Field(
        min_length=8, max_length=72, description="Senha com 8 a 72 caracteres"
    )


class UpdateUser(BaseModel):
    name: Nome | None = None
    email: EmailStr | None = None


class ResponseUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime
