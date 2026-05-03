from fastapi import APIRouter
import httpx

router = APIRouter()

@router.get("/wiki")
async def search_wiki(query: str):
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": query,
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "redirects": 1
    }
    headers = {
        "User-Agent": "Omnisverum/1.0 (contact@omnisverum.com)"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10)
            text = response.text
            data = response.json()
            pages = data["query"]["pages"]
            page = next(iter(pages.values()))
            return {
                "title": page.get("title"),
                "summary": page.get("extract", "No information found")
            }
    except Exception as e:
        return {"error": str(e)}