from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schema.user_schema import CreateUser, ResponseUser, UpdateUser
from app.service.user import create_new_user, get_user_by_email, update_user, delete_user

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
def get_user_email(db: DbSession, email: str) -> User:
    return get_user_by_email(db, email)


@router.patch(
    "/{user_id}",
    response_model=ResponseUser,
    status_code=status.HTTP_200_OK
)
def update_current_user(user_id: int, dados: UpdateUser, db: DbSession):
    return update_user(db, user_id, dados)

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def remover(user_id: int, db: DbSession):
    delete_user(db, user_id)