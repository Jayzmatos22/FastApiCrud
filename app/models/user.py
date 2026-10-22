from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, Boolean, DateTime, CheckConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass

class User(DeclarativeBase):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(name) >= 2", name ="ck_users_name_min")
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), Unique=True, index=True nullable=False)
    hash_password: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

