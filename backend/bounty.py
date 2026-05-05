import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import User, Bounty, Server, ServerMember, Reputation, get_db
from auth import get_current_user_id

router = APIRouter()


class CreateBountyBody(BaseModel):
    server_id: str
    title: str
    description: str
    reward_amount: int = 0


class CompleteBountyBody(BaseModel):
    bounty_id: str


@router.get("/bounties/{server_id}")
def get_server_bounties(server_id: str, db: Session = Depends(get_db)):
    """Get all bounties for a server."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    bounties = db.query(Bounty).filter(Bounty.server_id == server_id).all()
    
    result = []
    for bounty in bounties:
        creator = db.query(User).filter(User.id == bounty.created_by).first()
        completer = None
        if bounty.completed_by:
            completer = db.query(User).filter(User.id == bounty.completed_by).first()
        
        result.append({
            "id": bounty.id,
            "title": bounty.title,
            "description": bounty.description,
            "reward_amount": bounty.reward_amount,
            "is_completed": bounty.is_completed,
            "created_by": {
                "id": creator.id,
                "username": creator.username
            } if creator else None,
            "completed_by": {
                "id": completer.id,
                "username": completer.username
            } if completer else None,
            "created_at": bounty.created_at.strftime("%Y-%m-%d %H:%M"),
            "completed_at": bounty.completed_at.strftime("%Y-%m-%d %H:%M") if bounty.completed_at else None,
        })
    
    return {"server_id": server_id, "bounties": result}


@router.post("/bounties/create")
def create_bounty(
    body: CreateBountyBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new bounty."""
    if not body.title or not body.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    
    if not body.description or not body.description.strip():
        raise HTTPException(status_code=400, detail="Description is required")
    
    if body.reward_amount < 0:
        raise HTTPException(status_code=400, detail="Reward amount cannot be negative")
    
    # Check if server exists
    server = db.query(Server).filter(Server.id == body.server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if user is a member
    member = db.query(ServerMember).filter(
        ServerMember.server_id == body.server_id,
        ServerMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="You must be a server member to create bounties")
    
    bounty = Bounty(
        id=str(uuid.uuid4()),
        server_id=body.server_id,
        created_by=user_id,
        title=body.title.strip()[:100],
        description=body.description.strip()[:1000],
        reward_amount=body.reward_amount,
    )
    
    db.add(bounty)
    db.commit()
    
    return {"bounty_id": bounty.id, "message": "Bounty created successfully"}


@router.post("/bounties/complete")
def complete_bounty(
    body: CompleteBountyBody,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Mark a bounty as completed and award reputation."""
    bounty = db.query(Bounty).filter(Bounty.id == body.bounty_id).first()
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    
    if bounty.is_completed:
        raise HTTPException(status_code=400, detail="Bounty already completed")
    
    if bounty.created_by == user_id:
        raise HTTPException(status_code=400, detail="Cannot complete your own bounty")
    
    # Check if user is a server member
    member = db.query(ServerMember).filter(
        ServerMember.server_id == bounty.server_id,
        ServerMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="You must be a server member to complete bounties")
    
    # Mark bounty as completed
    bounty.is_completed = True
    bounty.completed_by = user_id
    bounty.completed_at = datetime.utcnow()
    
    # Award reputation to completer
    reputation = Reputation(
        id=str(uuid.uuid4()),
        from_user_id=bounty.created_by,
        to_user_id=user_id,
        server_id=bounty.server_id,
        value=bounty.reward_amount if bounty.reward_amount > 0 else 1,
        reason=f"Completed bounty: {bounty.title}",
    )
    db.add(reputation)
    
    db.commit()
    
    return {"message": "Bounty completed successfully", "reputation_awarded": reputation.value}


@router.get("/bounties/my/{server_id}")
def get_my_bounties(
    server_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get bounties created by or completed by the current user."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    created_bounties = db.query(Bounty).filter(
        Bounty.server_id == server_id,
        Bounty.created_by == user_id
    ).all()
    
    completed_bounties = db.query(Bounty).filter(
        Bounty.server_id == server_id,
        Bounty.completed_by == user_id
    ).all()
    
    return {
        "created": [
            {
                "id": b.id,
                "title": b.title,
                "reward_amount": b.reward_amount,
                "is_completed": b.is_completed,
                "created_at": b.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for b in created_bounties
        ],
        "completed": [
            {
                "id": b.id,
                "title": b.title,
                "reward_amount": b.reward_amount,
                "completed_at": b.completed_at.strftime("%Y-%m-%d %H:%M"),
            }
            for b in completed_bounties
        ]
    }
