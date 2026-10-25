from fastapi import FastAPI

from app.database import Base, engine
from app.models.user import User  # noqa: F401 - registra a tabela no metadata
from app.routers import usuarios

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastApiCrud")

app.include_router(usuarios.router)
