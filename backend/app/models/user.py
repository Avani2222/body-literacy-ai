from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    birthdate = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    