# Naver Search Open API 대신 상품명을 기반으로 네이버 쇼핑 검색 URL을 생성하도록 변경

from urllib.parse import quote


def search_shopping(query: str):
    if not query:
        return None

    return f"https://search.shopping.naver.com/search/all?query={quote(query)}"

# ---------------------------------------------------------------
# 기존 코드
 
# import requests
# from app.core.config import settings

# def search_shopping(query: str):
#     url = "https://openapi.naver.com/v1/search/shop.json"
#     headers = {
#         "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
#         "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
#     }
#     params = {"query": query, "display": 1}
    
#     response = requests.get(url, headers=headers, params=params)
#     response.raise_for_status()
    
#     data = response.json()
#     items = data.get("items", [])
    
#     if not items:
#         return None
    
#     return items[0].get("link")