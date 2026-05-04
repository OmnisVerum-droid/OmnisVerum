import os
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omnisverum.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    reputation = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    age_confirmed = Column(Boolean, default=False)
    tos_agreed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    display_name = Column(String)
    bio = Column(String, default="")
    is_anonymous = Column(Boolean, default=False)


class Server(Base):
    __tablename__ = "servers"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(String)
    owner_id = Column(String, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    invite_only = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ServerMember(Base):
    __tablename__ = "server_members"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id"))
    user_id = Column(String, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)


class Upload(Base):
    __tablename__ = "uploads"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id"))
    user_id = Column(String, ForeignKey("users.id"))
    content = Column(String)
    is_anonymous = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Invite(Base):
    __tablename__ = "invites"
    
    id = Column(String, primary_key=True)
    server_id = Column(String, ForeignKey("servers.id"))
    created_by = Column(String, ForeignKey("users.id"))
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
