import requests

from app.core.config import settings


def search_place(query: str):

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    headers = {
        "Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"
    }

    params = {
        "query": query
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )
    response.raise_for_status()

    data = response.json()

    if "documents" not in data:
        return {
            "success": False,
            "error": data
        }

    if not data["documents"]:
        return {
            "success": False,
            "message": "검색 결과 없음"
        }

    return {
        "success": True,
        "places": [
            {
                "place_name": p["place_name"],
                "address": p["address_name"],
                "latitude": p["y"],
                "longitude": p["x"],
                "place_url": p["place_url"]
            }
            for p in data["documents"]
        ]
    }