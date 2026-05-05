import os
import uuid
from typing import Annotated

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import User, UserProfile, get_db

router = APIRouter()

SECRET_KEY = os.getenv("OMNISVERUM_SECRET_KEY", "omnisverum_secret")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def require_admin_key(admin_key: str) -> None:
    expected = os.getenv("OMNISVERUM_ADMIN_KEY", "omnisverum_admin_key")
    if admin_key != expected:
        raise HTTPException(status_code=403, detail="Invalid admin key")


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))


def create_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            raise HTTPException(status_code=401, detail="Invalid token")
        return sub
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Session = Depends(get_db),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account locked")
    return user_id


class RegisterBody(BaseModel):
    username: str
    password: str
    age_confirmed: bool
    tos_agreed: bool


class LoginBody(BaseModel):
    username: str
    password: str


class ProfileUpdateBody(BaseModel):
    display_name: str
    bio: str = ""
    is_anonymous: bool = False


@router.post("/register")
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if not body.age_confirmed or not body.tos_agreed:
        raise HTTPException(status_code=400, detail="Must confirm age and agree to TOS")
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username taken")
    user = User(
        id=str(uuid.uuid4()),
        username=body.username,
        password=hash_password(body.password),
        age_confirmed=body.age_confirmed,
        tos_agreed=body.tos_agreed,
    )
    db.add(user)
    db.add(UserProfile(id=str(uuid.uuid4()), user_id=user.id, display_name=body.username, bio="", is_anonymous=False))
    db.commit()
    return {"message": "Account created", "token": create_token(user.id)}


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account locked")
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(id=str(uuid.uuid4()), user_id=user.id, display_name=user.username, bio="", is_anonymous=False)
        db.add(profile)
        db.commit()
    return {
        "token": create_token(user.id),
        "reputation": user.reputation,
        "display_name": profile.display_name,
        "bio": profile.bio,
        "is_anonymous": profile.is_anonymous,
    }


@router.get("/profile")
def get_profile(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(id=str(uuid.uuid4()), user_id=user_id, display_name=user.username, bio="", is_anonymous=False)
        db.add(profile)
        db.commit()
    return {
        "user_id": user_id,
        "username": user.username,
        "display_name": profile.display_name,
        "bio": profile.bio,
        "is_anonymous": profile.is_anonymous,
        "reputation": user.reputation,
    }


@router.put("/profile")
def update_profile(
    body: ProfileUpdateBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(id=str(uuid.uuid4()), user_id=user_id, display_name=user.username, bio="", is_anonymous=False)
        db.add(profile)

    cleaned_name = body.display_name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Display name cannot be empty")

    profile.display_name = cleaned_name[:40]
    profile.bio = body.bio.strip()[:280]
    profile.is_anonymous = body.is_anonymous
    db.commit()
    return {"message": "Profile updated"}
