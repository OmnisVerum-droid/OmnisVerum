from fastapi import APIRouter

router = APIRouter()


@router.get("/bounties")
def get_bounties():
    """Get active bounties."""
    return {"bounties": []}
