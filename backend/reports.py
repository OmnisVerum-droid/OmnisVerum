import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Upload, get_db
from auth import get_current_user_id

router = APIRouter()


@router.post("/report")
def report_upload(
    upload_id: str,
    reason: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Report an upload for violation."""
    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Reason is required")
    
    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    # In a real system, this would store the report
    return {"message": "Report submitted successfully"}
