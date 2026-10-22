from fastapi import FastAPI
from app.routers import usuarios
from app.models.user import User

u: User = {"nome": "ajilton santos", "email": "jailt@gmail.com", "age": 23, "money":500}

app = FastAPI()

app.include_router(usuarios.router)



