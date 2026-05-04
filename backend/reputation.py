from fastapi import APIRouter

router = APIRouter()


@router.get("/reputation")
def get_reputation():
    """Get reputation information."""
    return {"reputation": 0}
