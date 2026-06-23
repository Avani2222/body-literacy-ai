from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserInput
from app.core.auth import get_current_user
from app.models.user import User as AuthUser
from app.core.db import SessionLocal
from app.services.ai_service import generate_insight
from app.models.user_data import UserData

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/insight")
def get_insight(data: UserInput, db: Session = Depends(get_db), current_user: AuthUser = Depends(get_current_user)):

    print("🔥 HIT ENDPOINT")   # <-- ADD THIS

    try:
        new_entry = UserData(
            user_id=current_user.id,
            cycle_phase=data.cycle_phase,
            mood=data.mood,
            energy=data.energy,
            sleep=data.sleep
        )

        db.add(new_entry)
        db.commit()

        print("✅ SAVED TO DB")   # <-- ADD THIS

        result = generate_insight(data, db, user_id=current_user.id)

        print("🧠 AI RESULT >>>", result)  # <-- THIS SHOULD PRINT

        return result

    except Exception as e:
        print("❌ ERROR:", e)
        db.rollback()
        return {"error": str(e)}