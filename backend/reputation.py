import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from database import User, Reputation, Server, ServerMember, get_db
from auth import get_current_user_id

router = APIRouter()


class GiveReputationBody(BaseModel):
    to_user_id: str
    server_id: str
    value: int  # +1 or -1
    reason: str = ""


@router.get("/reputation/{user_id}")
def get_user_reputation(user_id: str, db: Session = Depends(get_db)):
    """Get a user's reputation score."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate total reputation
    total_rep = db.query(func.coalesce(func.sum(Reputation.value), 0)).filter(
        Reputation.to_user_id == user_id
    ).scalar() or 0
    
    # Get reputation breakdown by server
    server_reps = db.query(
        Server.id,
        Server.name,
        func.coalesce(func.sum(Reputation.value), 0).label("reputation")
    ).join(Reputation, Server.id == Reputation.server_id).filter(
        Reputation.to_user_id == user_id
    ).group_by(Server.id, Server.name).all()
    
    return {
        "user_id": user_id,
        "total_reputation": total_rep,
        "server_reputations": [
            {"server_id": sr.id, "server_name": sr.name, "reputation": sr.reputation}
            for sr in server_reps
        ]
    }


@router.post("/reputation/give")
def give_reputation(
    body: GiveReputationBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Give reputation to another user."""
    if body.value not in [-1, 1]:
        raise HTTPException(status_code=400, detail="Reputation value must be -1 or 1")
    
    if body.to_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot give reputation to yourself")
    
    # Check if target user exists
    target_user = db.query(User).filter(User.id == body.to_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Check if server exists
    server = db.query(Server).filter(Server.id == body.server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if both users are members of the server
    user_member = db.query(ServerMember).filter(
        ServerMember.server_id == body.server_id,
        ServerMember.user_id == user_id,
    ).first()
    
    target_member = db.query(ServerMember).filter(
        ServerMember.server_id == body.server_id,
        ServerMember.user_id == body.to_user_id,
    ).first()
    
    if not user_member or not target_member:
        raise HTTPException(status_code=403, detail="Both users must be server members")
    
    # Check if user already gave reputation to this user in this server
    existing = db.query(Reputation).filter(
        Reputation.from_user_id == user_id,
        Reputation.to_user_id == body.to_user_id,
        Reputation.server_id == body.server_id,
    ).first()
    
    if existing:
        # Update existing reputation
        existing.value = body.value
        existing.reason = body.reason
    else:
        # Create new reputation entry
        reputation = Reputation(
            id=str(uuid.uuid4()),
            from_user_id=user_id,
            to_user_id=body.to_user_id,
            server_id=body.server_id,
            value=body.value,
            reason=body.reason,
        )
        db.add(reputation)
    
    db.commit()
    
    # Update user's total reputation
    total_rep = db.query(func.coalesce(func.sum(Reputation.value), 0)).filter(
        Reputation.to_user_id == body.to_user_id
    ).scalar() or 0
    
    target_user.reputation = total_rep
    db.commit()
    
    return {"message": "Reputation given successfully", "new_total": total_rep}


@router.get("/reputation/server/{server_id}")
def get_server_reputation_leaderboard(
    server_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get reputation leaderboard for a server."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    leaderboard = db.query(
        User.id,
        User.username,
        func.coalesce(func.sum(Reputation.value), 0).label("reputation")
    ).join(Reputation, User.id == Reputation.to_user_id).filter(
        Reputation.server_id == server_id
    ).group_by(User.id, User.username).order_by(
        func.sum(Reputation.value).desc()
    ).limit(limit).all()
    
    return {
        "server_id": server_id,
        "server_name": server.name,
        "leaderboard": [
            {
                "user_id": entry.id,
                "username": entry.username,
                "reputation": entry.reputation
            }
            for entry in leaderboard
        ]
    }
