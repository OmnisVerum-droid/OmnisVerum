from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, User
from passlib.context import CryptContext
from jose import jwt
import uuid
import bcrypt

router = APIRouter()
SECRET_KEY = "omnisverum_secret"

def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8')[:72], hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id}, SECRET_KEY, algorithm="HS256")

@router.post("/register")
def register(username: str, password: str, age_confirmed: bool, tos_agreed: bool, db: Session = Depends(get_db)):
    if not age_confirmed or not tos_agreed:
        raise HTTPException(status_code=400, detail="Must confirm age and agree to TOS")
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username taken")
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        password=hash_password(password),
        age_confirmed=age_confirmed,
        tos_agreed=tos_agreed
    )
    db.add(user)
    db.commit()
    return {"message": "Account created", "token": create_token(user.id)}

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"token": create_token(user.id), "reputation": user.reputation}