from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, User
from uploads import Upload
from reports import Report
from servers import Server
import uuid

router = APIRouter()

ADMIN_KEY = "omnisverum_admin_key"

def verify_admin(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

@router.get("/admin/users")
def get_all_users(admin_key: str, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    users = db.query(User).all()
    return users

@router.get("/admin/reports")
def get_all_reports(admin_key: str, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    reports = db.query(Report).all()
    return reports

@router.post("/admin/lock_user")
def lock_user(admin_key: str, user_id: str, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_locked = True
    db.commit()
    return {"message": f"User {user_id} locked"}

@router.post("/admin/unlock_user")
def unlock_user(admin_key: str, user_id: str, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_locked = False
    user.reputation = 0
    db.commit()
    return {"message": f"User {user_id} unlocked"}

@router.delete("/admin/delete_upload")
def delete_upload(admin_key: str, upload_id: str, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    db.delete(upload)
    db.commit()
    return {"message": "Upload deleted"}

@router.delete("/admin/delete_server")
def delete_server(admin_key: str, server_id: str, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(server)
    db.commit()
    return {"message": "Server deleted"}

@router.post("/admin/adjust_reputation")
def adjust_reputation(admin_key: str, user_id: str, amount: float, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.reputation += amount
    db.commit()
    return {"message": f"Reputation adjusted", "new_reputation": user.reputation}

@router.post("/admin/shutdown")
def shutdown(admin_key: str, level: str, db: Session = Depends(get_db)):
    verify_admin(admin_key)
    levels = ["pause", "lockdown", "maintenance", "emergency", "full"]
    if level not in levels:
        raise HTTPException(status_code=400, detail=f"Invalid level. Choose from: {levels}")
    return {"message": f"Shutdown level '{level}' triggered", "status": "Platform shutting down"}