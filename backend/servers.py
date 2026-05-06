import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Server, ServerMember, Invite, Upload, User, get_db
from auth import get_current_user_id

router = APIRouter()


@router.post("/create")
def create_server(
    name: str,
    description: str,
    is_public: bool = True,
    invite_only: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new server."""
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="Server name is required")
    
    server = Server(
        id=str(uuid.uuid4()),
        name=name.strip()[:100],
        description=description.strip()[:500],
        owner_id=user_id,
        is_public=is_public,
        invite_only=invite_only,
    )
    db.add(server)
    db.commit()
    
    # Add owner as member
    member = ServerMember(
        id=str(uuid.uuid4()),
        server_id=server.id,
        user_id=user_id,
    )
    db.add(member)
    db.commit()
    
    return {"server_id": server.id, "name": server.name}


@router.get("/")
def list_servers(db: Session = Depends(get_db)):
    """List all public servers."""
    servers = db.query(Server).filter(Server.is_public == True).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "owner_id": s.owner_id,
            "invite_only": s.invite_only,
        }
        for s in servers
    ]


@router.post("/join")
def join_server(
    server_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Join a server."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if user is already a member
    existing = db.query(ServerMember).filter(
        ServerMember.server_id == server_id,
        ServerMember.user_id == user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this server")
    
    # Add user as member
    member = ServerMember(
        id=str(uuid.uuid4()),
        server_id=server_id,
        user_id=user_id,
    )
    db.add(member)
    db.commit()
    
    return {"message": "Successfully joined server"}


@router.post("/invite/create")
def create_invite(
    server_id: str,
    expires_hours: int = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Generate an invite link for a server."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Verify user is owner or admin
    if server.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only server owner can create invites")
    
    expires_at = None
    if expires_hours:
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    
    invite = Invite(
        id=str(uuid.uuid4()),
        server_id=server_id,
        created_by=user_id,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    
    invite_link = f"https://omnis-verum.vercel.app?invite={invite.id}"
    expires_str = expires_at.strftime("%Y-%m-%d %H:%M UTC") if expires_at else "Never"
    
    return {
        "invite_link": invite_link,
        "invite_id": invite.id,
        "expires": expires_str,
    }


@router.post("/join-by-invite")
def join_by_invite(
    invite_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Join a server using an invite link."""
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite")
    
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite has expired")
    
    server = db.query(Server).filter(Server.id == invite.server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if already member
    existing = db.query(ServerMember).filter(
        ServerMember.server_id == invite.server_id,
        ServerMember.user_id == user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")
    
    # Add as member
    member = ServerMember(
        id=str(uuid.uuid4()),
        server_id=invite.server_id,
        user_id=user_id,
    )
    db.add(member)
    db.commit()
    
    return {"message": "Joined server successfully", "server_id": server.id}
