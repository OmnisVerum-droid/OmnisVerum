import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Upload, User, UserProfile, Server, ServerMember, get_db
from auth import get_current_user_id

router = APIRouter()


@router.post("/upload")
def upload_text(
    server_id: str,
    content: str,
    is_anonymous: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Upload text content to a server."""
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    # Check if server exists
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if user is a member of the server
    member = db.query(ServerMember).filter(
        ServerMember.server_id == server_id,
        ServerMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="You are not a member of this server")
    
    upload = Upload(
        id=str(uuid.uuid4()),
        server_id=server_id,
        user_id=user_id,
        content=content.strip()[:5000],
        is_anonymous=is_anonymous,
    )
    db.add(upload)
    db.commit()
    
    return {"upload_id": upload.id, "message": "Content uploaded successfully"}


@router.get("/uploads/{server_id}")
def get_uploads(server_id: str, db: Session = Depends(get_db)):
    """Get all uploads for a server."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    uploads = db.query(Upload).filter(Upload.server_id == server_id).all()
    
    result = []
    for u in uploads:
        user = db.query(User).filter(User.id == u.user_id).first()
        profile = db.query(UserProfile).filter(UserProfile.user_id == u.user_id).first()
        
        display_name = "Anonymous" if u.is_anonymous else (profile.display_name if profile else user.username)
        
        result.append({
            "id": u.id,
            "content": u.content,
            "display_name": display_name,
            "timestamp": u.timestamp.strftime("%Y-%m-%d %H:%M"),
        })
    
    return result
