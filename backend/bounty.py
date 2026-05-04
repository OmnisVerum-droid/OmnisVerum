import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Boolean, Column, Float, String
from sqlalchemy.orm import Session

from auth import get_current_user_id
from database import Base, User, get_db
from reputation import get_permissions, get_tier

router = APIRouter()

class Bounty(Base):
    __tablename__ = "bounties"
    id = Column(String, primary_key=True)
    server_id = Column(String)
    posted_by = Column(String)
    question = Column(String)
    reward = Column(Float)
    is_claimed = Column(Boolean, default=False)
    claimed_by = Column(String, nullable=True)
    is_expired = Column(Boolean, default=False)

@router.post("/bounty/create")
def create_bounty(
    server_id: str,
    question: str,
    reward: float,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tier = get_tier(user.reputation)
    permissions = get_permissions(tier)
    if not permissions["can_post_bounty"]:
        raise HTTPException(status_code=403, detail="You need Verified tier or above to post bounties")
    if user.reputation < reward:
        raise HTTPException(status_code=400, detail="Not enough reputation points for this bounty")
    user.reputation -= reward
    bounty = Bounty(
        id=str(uuid.uuid4()),
        server_id=server_id,
        posted_by=user_id,
        question=question,
        reward=reward,
        is_claimed=False
    )
    db.add(bounty)
    db.commit()
    return {"message": "Bounty posted", "bounty_id": bounty.id}

@router.post("/bounty/claim")
def claim_bounty(bounty_id: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bounty = db.query(Bounty).filter(Bounty.id == bounty_id).first()
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    if bounty.is_claimed:
        raise HTTPException(status_code=400, detail="Bounty already claimed")
    if bounty.is_expired:
        raise HTTPException(status_code=400, detail="Bounty has expired")
    if bounty.posted_by == user_id:
        raise HTTPException(status_code=400, detail="Cannot claim your own bounty")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.reputation += bounty.reward
    bounty.is_claimed = True
    bounty.claimed_by = user_id
    db.commit()
    return {"message": "Bounty claimed", "reward": bounty.reward}

@router.post("/bounty/expire")
def expire_bounty(bounty_id: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    bounty = db.query(Bounty).filter(Bounty.id == bounty_id).first()
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    if bounty.posted_by != user_id:
        raise HTTPException(status_code=403, detail="Only the poster can expire this bounty")
    if bounty.is_claimed:
        raise HTTPException(status_code=400, detail="Bounty already claimed")
    poster = db.query(User).filter(User.id == bounty.posted_by).first()
    poster.reputation += bounty.reward
    bounty.is_expired = True
    db.commit()
    return {"message": "Bounty expired, points returned"}

@router.get("/bounties/{server_id}")
def list_bounties(server_id: str, db: Session = Depends(get_db)):
    bounties = db.query(Bounty).filter(
        Bounty.server_id == server_id,
        Bounty.is_claimed == False,
        Bounty.is_expired == False
    ).all()
    return bounties