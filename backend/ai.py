from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Server, ServerMember, Upload, get_db
from auth import get_current_user_id

router = APIRouter()


@router.post("/ask")
def ask_ai(
    server_id: str,
    question: str,
    want_other_sources: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Ask the AI a question based on server uploads."""
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Check if server exists
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Check if user is a member
    member = db.query(ServerMember).filter(
        ServerMember.server_id == server_id,
        ServerMember.user_id == user_id,
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="You are not a member of this server")
    
    # Get all uploads for the server
    uploads = db.query(Upload).filter(Upload.server_id == server_id).all()
    
    if not uploads:
        return {
            "answer": "No data in this server yet. Start by uploading information.",
            "sources": []
        }
    
    # Simple RAG: match question keywords with upload content
    question_lower = question.lower()
    relevant_uploads = [
        u for u in uploads
        if any(word in u.content.lower() for word in question_lower.split())
    ]
    
    if not relevant_uploads:
        relevant_uploads = uploads[:3]  # Return first 3 uploads if no match
    
    # Generate a simple answer from relevant uploads
    answer = f"Based on the knowledge in {server.name}, I found the following relevant information:\n\n"
    answer += "\n\n".join([u.content[:200] for u in relevant_uploads[:3]])
    
    return {
        "answer": answer,
        "sources": [u.id for u in relevant_uploads[:3]]
    }
