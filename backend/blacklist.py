from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, String
from sqlalchemy.orm import Session
from database import get_db, Base
import uuid

router = APIRouter()

class PersonalBlacklist(Base):
    __tablename__ = "personal_blacklist"
    id = Column(String, primary_key=True)
    owner_id = Column(String)
    blocked_user_id = Column(String)

class ServerBlacklist(Base):
    __tablename__ = "server_blacklist"
    id = Column(String, primary_key=True)
    server_id = Column(String)
    blocked_user_id = Column(String)
    banned_by = Column(String)

@router.post("/blacklist/personal/add")
def personal_blacklist_add(owner_id: str, blocked_user_id: str, db: Session = Depends(get_db)):
    if owner_id == blocked_user_id:
        raise HTTPException(status_code=400, detail="Cannot blacklist yourself")
    existing = db.query(PersonalBlacklist).filter(
        PersonalBlacklist.owner_id == owner_id,
        PersonalBlacklist.blocked_user_id == blocked_user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already blacklisted")
    entry = PersonalBlacklist(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        blocked_user_id=blocked_user_id
    )
    db.add(entry)
    db.commit()
    return {"message": "User blacklisted personally"}

@router.post("/blacklist/server/add")
def server_blacklist_add(server_id: str, banned_by: str, blocked_user_id: str, db: Session = Depends(get_db)):
    if banned_by == blocked_user_id:
        raise HTTPException(status_code=400, detail="Cannot blacklist yourself")
    existing = db.query(ServerBlacklist).filter(
        ServerBlacklist.server_id == server_id,
        ServerBlacklist.blocked_user_id == blocked_user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already blacklisted from server")
    entry = ServerBlacklist(
        id=str(uuid.uuid4()),
        server_id=server_id,
        blocked_user_id=blocked_user_id,
        banned_by=banned_by
    )
    db.add(entry)
    db.commit()
    return {"message": "User blacklisted from server"}

@router.get("/blacklist/check")
def check_blacklist(viewer_id: str, upload_owner_id: str, server_id: str, db: Session = Depends(get_db)):
    personal = db.query(PersonalBlacklist).filter(
        PersonalBlacklist.owner_id == upload_owner_id,
        PersonalBlacklist.blocked_user_id == viewer_id
    ).first()
    server = db.query(ServerBlacklist).filter(
        ServerBlacklist.server_id == server_id,
        ServerBlacklist.blocked_user_id == viewer_id
    ).first()
    return {
        "personally_blacklisted": personal is not None,
        "server_blacklisted": server is not None,
        "can_see_content": personal is None and server is None
    }

class PostBlacklist(Base):
    __tablename__ = "post_blacklist"
    id = Column(String, primary_key=True)
    upload_id = Column(String)
    blocked_user_id = Column(String)
    owner_id = Column(String)

@router.post("/blacklist/post/add")
def post_blacklist_add(upload_id: str, owner_id: str, blocked_user_id: str, db: Session = Depends(get_db)):
    if owner_id == blocked_user_id:
        raise HTTPException(status_code=400, detail="Cannot blacklist yourself")
    existing = db.query(PostBlacklist).filter(
        PostBlacklist.upload_id == upload_id,
        PostBlacklist.blocked_user_id == blocked_user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already blacklisted from this post")
    entry = PostBlacklist(
        id=str(uuid.uuid4()),
        upload_id=upload_id,
        owner_id=owner_id,
        blocked_user_id=blocked_user_id
    )
    db.add(entry)
    db.commit()
    return {"message": "User blacklisted from this post"}

@router.get("/blacklist/post/check")
def check_post_blacklist(upload_id: str, viewer_id: str, db: Session = Depends(get_db)):
    blocked = db.query(PostBlacklist).filter(
        PostBlacklist.upload_id == upload_id,
        PostBlacklist.blocked_user_id == viewer_id
    ).first()
    return {"can_see_post": blocked is None}