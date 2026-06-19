from sqlalchemy import Column, Integer, String
from app.core.db import Base

class UserData(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    cycle_phase = Column(String)
    mood = Column(String)
    energy = Column(String)
    sleep = Column(String)