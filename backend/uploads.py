from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import Session
from database import get_db, Base, User
from datetime import datetime
import uuid

router = APIRouter()

class Upload(Base):
    __tablename__ = "uploads"
    id = Column(String, primary_key=True)
    server_id = Column(String)
    user_id = Column(String)
    display_name = Column(String)
    content = Column(String)
    is_anonymous = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    timestamp = Column(String)

@router.post("/upload")
def upload_text(server_id: str, user_id: str, content: str, is_anonymous: bool, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_locked:
        raise HTTPException(status_code=403, detail="Account locked due to negative reputation")
    if user.reputation < 0:
        raise HTTPException(status_code=403, detail="Reputation too low to upload")
    display_name = "Anonymous" if is_anonymous else user.username
    upload = Upload(
        id=str(uuid.uuid4()),
        server_id=server_id,
        user_id=user_id,
        display_name=display_name,
        content=content,
        is_anonymous=is_anonymous,
        timestamp=str(datetime.now())
    )
    db.add(upload)
    db.commit()
    return {"message": "Upload successful", "upload_id": upload.id}

@router.get("/uploads/{server_id}")
def get_uploads(server_id: str, db: Session = Depends(get_db)):
    uploads = db.query(Upload).filter(Upload.server_id == server_id).all()
    return uploads