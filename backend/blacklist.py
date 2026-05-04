from fastapi import APIRouter

router = APIRouter()


@router.get("/blacklist")
def get_blacklist():
    """Get user's personal blacklist."""
    return {"blacklist": []}
