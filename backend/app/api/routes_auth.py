from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import os
from pydantic import BaseModel

from app.core.auth import get_db, get_password_hash, create_access_token, authenticate_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

@router.post("/signup", status_code=201)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=request.name,
        email=request.email,
        hashed_password=get_password_hash(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # return token immediately so frontend logs user in after signup
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Accepts either JSON {"email": "...", "password": "..."} (frontend)
    or form-encoded fields (username/password) used by OAuth2 clients.
    Returns an access token on success.
    """
    # Determine content type and extract credentials
    content_type = request.headers.get("content-type", "")
    email = None
    password = None
    print("yes, login endpoint hit")

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
        email = body.get("email") or body.get("username")
        password = body.get("password")
    else:
        # try form data (OAuth2PasswordRequestForm sends form-encoded)
        form = await request.form()
        # OAuth2 uses "username" field; some clients might use "email"
        email = form.get("username") or form.get("email")
        password = form.get("password")
    print(body)
    if not email or not password:
        raise HTTPException(status_code=422, detail="Email and password required")

    user = authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)))
    )
    print("Login successful, token generated:", access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 token endpoint (keeps compatibility with OAuth2PasswordRequestForm clients).
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)))
    access_token = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Simple health check endpoint.
    Returns JSON indicating service liveness and DB connectivity.
    """
    result = {"status": "ok", "db": "ok"}
    try:
        # lightweight DB check
        db.execute("SELECT 1")
    except Exception as e:
        result["status"] = "error"
        result["db"] = "error"
        result["error"] = str(e)
    return result

