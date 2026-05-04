from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import require_admin_key

router = APIRouter()


@router.post("/admin/verify")
def verify_admin(admin_key: str):
    """Verify admin access."""
    try:
        require_admin_key(admin_key)
        return {"message": "Admin verified"}
    except HTTPException:
        raise HTTPException(status_code=403, detail="Invalid admin key")
