from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, User

router = APIRouter()

def get_tier(reputation: float) -> str:
    if reputation >= 1000:
        return "Authority"
    elif reputation >= 501:
        return "Verified"
    elif reputation >= 201:
        return "Trusted"
    elif reputation >= 51:
        return "Member"
    elif reputation >= 0:
        return "Newcomer"
    elif reputation >= -50:
        return "Flagged"
    else:
        return "Locked"

def get_permissions(tier: str) -> dict:
    permissions = {
        "Authority": {
            "can_upload": True,
            "can_vote": True,
            "can_post_bounty": True,
            "can_moderate": True,
            "can_post_links": True,
            "ai_trust": 1.0
        },
        "Verified": {
            "can_upload": True,
            "can_vote": True,
            "can_post_bounty": True,
            "can_moderate": False,
            "can_post_links": True,
            "ai_trust": 0.8
        },
        "Trusted": {
            "can_upload": True,
            "can_vote": True,
            "can_post_bounty": False,
            "can_moderate": False,
            "can_post_links": True,
            "ai_trust": 0.6
        },
        "Member": {
            "can_upload": True,
            "can_vote": True,
            "can_post_bounty": False,
            "can_moderate": False,
            "can_post_links": False,
            "ai_trust": 0.4
        },
        "Newcomer": {
            "can_upload": False,
            "can_vote": False,
            "can_post_bounty": False,
            "can_moderate": False,
            "can_post_links": False,
            "ai_trust": 0.2
        },
        "Flagged": {
            "can_upload": False,
            "can_vote": False,
            "can_post_bounty": False,
            "can_moderate": False,
            "can_post_links": False,
            "ai_trust": 0.0
        },
        "Locked": {
            "can_upload": False,
            "can_vote": False,
            "can_post_bounty": False,
            "can_moderate": False,
            "can_post_links": False,
            "ai_trust": 0.0
        }
    }
    return permissions[tier]

@router.get("/reputation/{user_id}")
def get_reputation(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    tier = get_tier(user.reputation)
    permissions = get_permissions(tier)
    return {
        "user_id": user_id,
        "reputation": user.reputation,
        "tier": tier,
        "permissions": permissions
    }

@router.post("/vote")
def vote(upload_id: str, voter_id: str, is_upvote: bool, db: Session = Depends(get_db)):
    voter = db.query(User).filter(User.id == voter_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Voter not found")
    voter_tier = get_tier(voter.reputation)
    voter_permissions = get_permissions(voter_tier)
    if not voter_permissions["can_vote"]:
        raise HTTPException(status_code=403, detail="Your reputation is too low to vote")
    from uploads import Upload
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    uploader = db.query(User).filter(User.id == upload.user_id).first()
    if not uploader:
        raise HTTPException(status_code=404, detail="Uploader not found")
    if is_upvote:
        uploader.reputation += 1
    else:
        uploader.reputation -= 1
    if uploader.reputation < -50:
        uploader.is_locked = True
    db.commit()
    tier = get_tier(uploader.reputation)
    return {
        "message": "Vote recorded",
        "uploader_reputation": uploader.reputation,
        "uploader_tier": tier,
        "is_locked": uploader.is_locked
    }