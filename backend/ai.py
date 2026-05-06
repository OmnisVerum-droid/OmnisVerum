import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import chromadb
import torch
from sentence_transformers import SentenceTransformer

from database import Server, ServerMember, Upload, get_db
from auth import get_current_user_id

router = APIRouter()

# Global variables for lazy loading
_chroma_client: Optional[chromadb.PersistentClient] = None
_embedding_model = None

def get_chroma_client():
    """Get or create ChromaDB client with lazy loading."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path="./chroma_db")
    return _chroma_client

def get_embedding_model():
    """Get or create embedding model with lazy loading and CPU optimization."""
    global _embedding_model
    if _embedding_model is None:
        # Use lightweight model and force CPU usage
        device = "cpu"
        _embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2', device=device)
    return _embedding_model


def get_or_create_collection(server_id: str):
    """Get or create a ChromaDB collection for a server."""
    client = get_chroma_client()
    try:
        collection = client.get_collection(name=f"server_{server_id}")
    except:
        collection = client.create_collection(
            name=f"server_{server_id}",
            metadata={"hnsw:space": "cosine"}
        )
    return collection


def update_server_embeddings(server_id: str, db: Session):
    """Update ChromaDB embeddings for all uploads in a server."""
    collection = get_or_create_collection(server_id)
    uploads = db.query(Upload).filter(Upload.server_id == server_id).all()
    
    if not uploads:
        return
    
    # Clear existing embeddings
    try:
        collection.delete()
    except:
        pass
    
    # Process in batches to optimize memory
    batch_size = 8
    for i in range(0, len(uploads), batch_size):
        batch = uploads[i:i+batch_size]
        documents = [upload.content for upload in batch]
        metadatas = [{"upload_id": upload.id, "user_id": upload.user_id} for upload in batch]
        ids = [upload.id for upload in batch]
        
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )


@router.post("/ask")
def ask_ai(
    server_id: str,
    question: str,
    want_other_sources: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Ask the AI a question based on server uploads using semantic search."""
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
    
    # Update embeddings if needed
    collection = get_or_create_collection(server_id)
    
    try:
        # Perform semantic search
        results = collection.query(
            query_texts=[question],
            n_results=5
        )
        
        if not results['documents'][0]:
            # Fallback to recent uploads if no results
            relevant_uploads = uploads[:3]
        else:
            # Get upload objects from results
            upload_ids = results['metadatas'][0]
            relevant_uploads = []
            for metadata in upload_ids:
                upload = db.query(Upload).filter(Upload.id == metadata['upload_id']).first()
                if upload:
                    relevant_uploads.append(upload)
        
        if not relevant_uploads:
            relevant_uploads = uploads[:3]
        
        # Generate answer from relevant uploads
        answer = f"Based on the knowledge in {server.name}, here's what I found:\n\n"
        for i, upload in enumerate(relevant_uploads[:3], 1):
            answer += f"{i}. {upload.content[:300]}...\n\n"
        
        return {
            "answer": answer,
            "sources": [u.id for u in relevant_uploads[:3]],
            "search_type": "semantic"
        }
        
    except Exception as e:
        # Fallback to basic matching if semantic search fails
        question_lower = question.lower()
        relevant_uploads = [
            u for u in uploads
            if any(word in u.content.lower() for word in question_lower.split())
        ]
        
        if not relevant_uploads:
            relevant_uploads = uploads[:3]
        
        answer = f"Based on the knowledge in {server.name}, I found this information:\n\n"
        answer += "\n\n".join([u.content[:200] for u in relevant_uploads[:3]])
        
        return {
            "answer": answer,
            "sources": [u.id for u in relevant_uploads[:3]],
            "search_type": "keyword_fallback"
        }
