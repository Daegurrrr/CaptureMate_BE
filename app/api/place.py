from fastapi import APIRouter

from app.services.kakao_service import search_place

router = APIRouter()


@router.get("/search")
def place_search(query: str):

    result = search_place(query)

    return {
        "success": True,
        "data": result
    }