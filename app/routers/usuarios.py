from fastapi import APIRouter, Depends, status
from app.models.user import User
from app.service.user import create_new_user
from typing import annotated
from sqlalchemy.orm import Session

DbSession = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/usuarios",
            tags=["Usuarios"]
    )

@router.post("/registrar", response_model=ResponseUser, status_code=201)
def register(user: CreateUser, db: Session = Depends(get_db), ):
    return create_new_user(db, user)