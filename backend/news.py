from fastapi import APIRouter

router = APIRouter()


@router.get("/news")
def get_news():
    """Get platform news and updates."""
    return {"news": []}
