from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user_id
from database import get_db
from uploads import Upload
import chromadb
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

router = APIRouter()

chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("omnisverum")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

@router.post("/ask")
def ask_question(
    server_id: str,
    question: str,
    want_other_sources: bool = False,
    _user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    uploads = db.query(Upload).filter(Upload.server_id == server_id).all()
    if not uploads:
        raise HTTPException(status_code=404, detail="No data in this server yet")
    
    context = "\n".join([u.content for u in uploads])
    
    system_prompt = f"You are Omnisverum. Answer questions based only on this information:\n{context}"
    
    if want_other_sources:
        system_prompt += "\nAfter answering, suggest 2-3 types of external sources the user could check to verify this information. Do not make up specific links."

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    )
    return {"answer": response.choices[0].message.content}