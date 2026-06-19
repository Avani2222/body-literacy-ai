from pydantic import BaseModel
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class UserInput(BaseModel):
    user_id: str
    cycle_phase: str
    mood: str
    energy: str
    sleep: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Optional[str] = None
    timezone: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[int] = None