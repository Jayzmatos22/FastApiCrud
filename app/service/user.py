from app.schema.user_schema import CreateUser
from app.models.user import user
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select


pwd = CryptContext(schemes=["bcrypt"], deprecated="ato")

def create_new_user(db: Session, data_user: CreateUser) -> User:
    exist_user = db.scalar(select(User).where(User.email == data_user.email))
    if exist_user:
        raise HTTPException(status.HTTP_409_CONFLICT, "email já cadastrado")
    
    user = User(
        name = data_user.name,
        email = data_user.email,
        hash_password = data_user.hash_password
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.409_CONFLICT, "email já cadastrado")
    db.refresh(user)
    return user
        




