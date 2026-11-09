from fastapi import FastAPI

from app.database import Base, engine
from app.routers import usuarios

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastApiCrud")

app.include_router(usuarios.router)
