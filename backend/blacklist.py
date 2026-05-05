import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import User, Blacklist, Server, ServerMember, get_db
from auth import get_current_user_id

router = APIRouter()


class BlacklistBody(BaseModel):
    blocked_user_id: str
    server_id: str = None
    reason: str = ""


@router.get("/blacklist")
def get_my_blacklist(
    server_id: str = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get user's personal blacklist, optionally filtered by server."""
    query = db.query(Blacklist).filter(Blacklist.user_id == user_id)
    
    if server_id:
        query = query.filter(Blacklist.server_id == server_id)
    
    blacklists = query.all()
    
    result = []
    for bl in blacklists:
        blocked_user = db.query(User).filter(User.id == bl.blocked_user_id).first()
        server = None
        if bl.server_id:
            server = db.query(Server).filter(Server.id == bl.server_id).first()
        
        result.append({
            "id": bl.id,
            "blocked_user": {
                "id": blocked_user.id,
                "username": blocked_user.username
            } if blocked_user else None,
            "server": {
                "id": server.id,
                "name": server.name
            } if server else None,
            "reason": bl.reason,
            "created_at": bl.created_at.strftime("%Y-%m-%d %H:%M"),
        })
    
    return {"blacklist": result}


@router.post("/blacklist/add")
def add_to_blacklist(
    body: BlacklistBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a user to blacklist."""
    if body.blocked_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot blacklist yourself")
    
    # Check if target user exists
    target_user = db.query(User).filter(User.id == body.blocked_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If server-specific, check if server exists and user is member
    if body.server_id:
        server = db.query(Server).filter(Server.id == body.server_id).first()
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        
        member = db.query(ServerMember).filter(
            ServerMember.server_id == body.server_id,
            ServerMember.user_id == user_id,
        ).first()
        if not member:
            raise HTTPException(status_code=403, detail="You must be a server member to create server-specific blacklists")
    
    # Check if already blacklisted
    existing = db.query(Blacklist).filter(
        Blacklist.user_id == user_id,
        Blacklist.blocked_user_id == body.blocked_user_id,
        Blacklist.server_id == body.server_id,
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already blacklisted")
    
    blacklist = Blacklist(
        id=str(uuid.uuid4()),
        user_id=user_id,
        blocked_user_id=body.blocked_user_id,
        server_id=body.server_id,
        reason=body.reason.strip()[:200],
    )
    
    db.add(blacklist)
    db.commit()
    
    return {"message": "User added to blacklist successfully"}


@router.delete("/blacklist/{blacklist_id}")
def remove_from_blacklist(
    blacklist_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Remove a user from blacklist."""
    blacklist = db.query(Blacklist).filter(
        Blacklist.id == blacklist_id,
        Blacklist.user_id == user_id,
    ).first()
    
    if not blacklist:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    
    db.delete(blacklist)
    db.commit()
    
    return {"message": "User removed from blacklist successfully"}


@router.get("/blacklist/check/{user_id}")
def check_if_blacklisted(
    user_id: str,
    server_id: str = None,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Check if a user is blacklisted by the current user."""
    query = db.query(Blacklist).filter(
        Blacklist.user_id == current_user_id,
        Blacklist.blocked_user_id == user_id,
    )
    
    if server_id:
        # Check server-specific blacklist
        query = query.filter(Blacklist.server_id == server_id)
    else:
        # Check global blacklist (server_id is None)
        query = query.filter(Blacklist.server_id.is_(None))
    
    blacklist_entry = query.first()
    
    return {
        "is_blacklisted": blacklist_entry is not None,
        "reason": blacklist_entry.reason if blacklist_entry else None,
        "created_at": blacklist_entry.created_at.strftime("%Y-%m-%d %H:%M") if blacklist_entry else None,
    }
