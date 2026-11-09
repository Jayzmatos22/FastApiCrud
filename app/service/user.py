from fastapi import HTTPException, status
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schema.user_schema import CreateUser, UpdateUser

EMAIL_JA_CADASTRADO = "email já cadastrado"
USUARIO_NAO_ENCONTRADO = "usuário não encontrado"

pwd = PasswordHash((BcryptHasher(),))


def _get_active_user(db: Session, user_id: int) -> User:
    """Busca por id, tratando usuario inativo como inexistente."""
    user = db.get(User, user_id)
    if user is None or not user.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, USUARIO_NAO_ENCONTRADO)
    return user


def create_new_user(db: Session, data_user: CreateUser) -> User:
    exist_user = db.scalar(select(User).where(User.email == data_user.email))
    if exist_user:
        raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_JA_CADASTRADO)

    user = User(
        name=data_user.name,
        email=data_user.email,
        hash_password=pwd.hash(data_user.password),
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_JA_CADASTRADO) from exc
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, USUARIO_NAO_ENCONTRADO)
    return user


def update_user(db: Session, user_id: int, dados: UpdateUser) -> User:
    user = _get_active_user(db, user_id)

    novos = dados.model_dump(exclude_unset=True, exclude_none=True)

    novo_email = novos.get("email")
    if novo_email is not None:
        em_uso = db.scalar(
            select(User).where(User.email == novo_email, User.id != user_id)
        )
        if em_uso:
            raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_JA_CADASTRADO)

    for campo, valor in novos.items():
        setattr(user, campo, valor)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_JA_CADASTRADO) from exc
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    user = _get_active_user(db, user_id)
    user.active = False
    db.commit()
