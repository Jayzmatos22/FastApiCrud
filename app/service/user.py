from fastapi import HTTPException, status
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schema.user_schema import CreateUser

EMAIL_JA_CADASTRADO = "email já cadastrado"

pwd = PasswordHash((BcryptHasher(),))


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
