from sqlalchemy import create_engine, Column, String, Integer, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./omnisverum.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    reputation = Column(Float, default=0)
    is_anonymous = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    age_confirmed = Column(Boolean, default=False)
    tos_agreed = Column(Boolean, default=False)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    bio = Column(Text, default="")
    is_anonymous = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()