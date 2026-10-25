from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schema.user_schema import CreateUser, ResponseUser
from app.service.user import create_new_user, get_user_by_email

DbSession = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post(
    "/registrar",
    response_model=ResponseUser,
    status_code=status.HTTP_201_CREATED,
)
def register(user: CreateUser, db: DbSession) -> User:
    return create_new_user(db, user)


@router.get(
    "/{email}", response_model=ResponseUser,
    status_code=status.HTTP_200_OK
)
def read_user_by_email(db: DbSession, email: str) -> User:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
    return user