from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import Session
from database import get_db, Base
import uuid
import time

router = APIRouter()

class Server(Base):
    __tablename__ = "servers"
    id = Column(String, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    owner_id = Column(String)
    is_public = Column(Boolean, default=False)
    invite_only = Column(Boolean, default=False)

class ServerMember(Base):
    __tablename__ = "server_members"
    id = Column(String, primary_key=True)
    server_id = Column(String)
    user_id = Column(String)

class InviteLink(Base):
    __tablename__ = "invite_links"
    id = Column(String, primary_key=True)
    server_id = Column(String)
    created_by = Column(String)
    expires_at = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

@router.post("/servers/create")
def create_server(name: str, description: str, is_public: bool, invite_only: bool = False, owner_id: str = "", db: Session = Depends(get_db)):
    existing = db.query(Server).filter(Server.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Server name taken")
    server = Server(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        owner_id=owner_id,
        is_public=is_public,
        invite_only=invite_only
    )
    db.add(server)
    db.commit()
    return {"message": "Server created", "server_id": server.id}

@router.post("/servers/join")
def join_server(server_id: str, user_id: str, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if server.invite_only:
        raise HTTPException(status_code=403, detail="This server is invite only")
    already_member = db.query(ServerMember).filter(
        ServerMember.server_id == server_id,
        ServerMember.user_id == user_id
    ).first()
    if already_member:
        raise HTTPException(status_code=400, detail="Already a member")
    member = ServerMember(
        id=str(uuid.uuid4()),
        server_id=server_id,
        user_id=user_id
    )
    db.add(member)
    db.commit()
    return {"message": "Joined server"}

@router.get("/servers")
def list_servers(db: Session = Depends(get_db)):
    servers = db.query(Server).filter(Server.is_public == True).all()
    return servers

@router.post("/servers/invite/create")
def create_invite(server_id: str, user_id: str, expires_hours: int = None, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if server.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Only server owner can create invites")
    expires_at = None
    if expires_hours:
        expires_at = int(time.time()) + (expires_hours * 3600)
    invite = InviteLink(
        id=str(uuid.uuid4()),
        server_id=server_id,
        created_by=user_id,
        expires_at=expires_at,
        is_active=True
    )
    db.add(invite)
    db.commit()
    expiry_text = f"{expires_hours} hours" if expires_hours else "Never"
    return {
        "invite_link": f"http://127.0.0.1:8000/servers/join/invite/{invite.id}",
        "expires": expiry_text
    }

@router.get("/servers/join/invite/{invite_id}")
def join_via_invite(invite_id: str, user_id: str, db: Session = Depends(get_db)):
    invite = db.query(InviteLink).filter(InviteLink.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite link")
    if not invite.is_active:
        raise HTTPException(status_code=400, detail="Invite link is no longer active")
    if invite.expires_at and int(time.time()) > invite.expires_at:
        invite.is_active = False
        db.commit()
        raise HTTPException(status_code=400, detail="Invite link has expired")
    already_member = db.query(ServerMember).filter(
        ServerMember.server_id == invite.server_id,
        ServerMember.user_id == user_id
    ).first()
    if already_member:
        raise HTTPException(status_code=400, detail="Already a member")
    member = ServerMember(
        id=str(uuid.uuid4()),
        server_id=invite.server_id,
        user_id=user_id
    )
    db.add(member)
    db.commit()
    return {"message": "Joined server via invite"}