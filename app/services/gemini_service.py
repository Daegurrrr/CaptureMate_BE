# Gemini를 활용한 카테고리별 필드 추출 서비스

from datetime import datetime
import json
from urllib.parse import quote

from google import genai

from app.core.config import settings
from app.services.kakao_service import search_place
from app.services.naver_service import search_shopping

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def parse_dt(val):
    if val is None:
        return None

    try:
        return datetime.fromisoformat(val).isoformat()
    except Exception:
        return None


def build_google_map_url(query: str):
    if not query:
        return None

    return f"https://www.google.com/maps/search/?api=1&query={quote(query)}"


def build_google_search_url(query: str):
    if not query:
        return None

    return f"https://www.google.com/search?q={quote(query)}"


def build_prompt(category: str, ocr_text: str) -> str:
    prompts = {
        "쇼핑": f"""
당신은 쇼핑 스크린샷에서 상품 정보를 추출하는 AI입니다.
OCR에는 오타나 누락이 있을 수 있으므로 전체 문맥을 고려하세요.

규칙:

- 실제 판매 상품으로 확인되는 상품을 모두 추출하세요.
- 상품명은 최대한 정확하게 추출하세요.
- 장바구니, 찜, 전체, 삭제하기 같은 UI 문구는 상품명으로 추출하지 마세요.(영어로 번역했을 때 같은 의미를 가진 문구도 제외)
- 상품 개수, 수량, 가격 등의 숫자를 상품명에 포함하지 마세요.
- 브랜드명이나 쇼핑몰명이 확인되면 brand_name에 추출하세요.
- 브랜드명이나 쇼핑몰명이 검색에 도움이 되면 search_query에 포함하세요.
- 광고 문구와 설명 문구는 제외하세요.
- 알 수 없는 상품명은 임의로 만들지 마세요.
- 추출할 수 없는 필드는 null로 설정하세요.
- 반드시 순수 JSON만 출력하세요.

OCR:
{ocr_text}

형식:
{{
    "items": [
        {{
            "product_name": "...",
            "brand_name": "...",
            "search_query": "..."
        }}
    ]
}}
""",
        "장소": f"""
당신은 장소 스크린샷에서 실제 방문 가능한 장소 정보를 추출하는 AI입니다.
OCR에는 오타, 누락, 외국어 인식 오류가 있을 수 있으므로 전체 문맥을 고려하세요.

규칙:

- 확인되는 구체적인 장소를 모두 추출하세요.
- 호텔, 식당, 카페, 상점, 관광지 등 고유 장소명만 추출하세요.
- 경주, 서울, 도쿄처럼 도시명이나 지역명만 단독 장소로 추출하지 마세요.
- 주소에 포함된 지역명을 별도 장소로 만들지 마세요.
- 동일한 장소가 반복되면 하나로 합치세요.
- 장소명과 주소가 함께 있으면 하나의 item으로 합치세요.
- 서로 다른 실제 장소가 여러 개 있을 때만 여러 item을 반환하세요.
- place_name에는 OCR에서 확인되는 장소명을 최대한 그대로 사용하세요.
- 한글로 음차된 외국 상호명도 장소 후보로 반드시 검토하세요.
- 영문 대문자나 간판 문구를 무조건 장소명으로 판단하지 말고,
  다른 고유명사와 문맥을 비교해 실제 방문 장소를 추출하세요.
- OCR 장소명에 오타가 의심되면 corrected_place_name에 가장 가능성 높은 교정 후보를 반환하세요.
- 교정 근거가 부족하면 corrected_place_name은 null로 설정하세요.
- address에는 실제 주소만 포함하고 좋아요 수, 댓글 수, 시간 등의 숫자는 제외하세요.
- map_query는 Google 지도 검색에 적합한 장소명으로 생성하세요.
- 해외 장소는 현지어 또는 공식 영문명을 우선 사용하세요.
- 실제 장소를 알 수 없으면 임의로 만들어내지 마세요.
- 반드시 순수 JSON만 출력하세요.

OCR:
{ocr_text}

형식:
{{
    "items": [
        {{
            "place_name": "...",
            "corrected_place_name": "...",
            "address": "...",
            "map_query": "..."
        }}
    ]
}}
""",
        "일정": f"""
당신은 일정 스크린샷에서 일정 정보를 추출하는 AI입니다.

규칙:

- 확인되는 모든 일정을 추출하세요.
- 일정마다 title, start_at, end_at을 반환하세요.
- 날짜에 연도가 없으면 2026년으로 가정하세요.
- 종료 시간이 없으면 end_at은 null입니다.
- 추출할 수 없는 필드는 null로 설정하세요.
- 반드시 순수 JSON만 출력하세요.

OCR:
{ocr_text}

형식:
{{
    "items": [
        {{
            "title": "...",
            "start_at": "YYYY-MM-DDTHH:MM:SS",
            "end_at": "YYYY-MM-DDTHH:MM:SS"
        }}
    ]
}}
""",
        "메모": f"""
당신은 메모 스크린샷에서 제목과 핵심 내용을 추출하는 AI입니다.
추출할 수 없는 필드는 null로 설정하세요.
반드시 순수 JSON만 출력하세요.

OCR:
{ocr_text}

형식:
{{
    "title": "...",
    "content": "..."
}}
""",
    }

    return prompts.get(category, prompts["메모"])


async def analyze_with_gemini(category: str, ocr_text: str) -> dict:
    prompt = build_prompt(category, ocr_text)

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "temperature": 0,
            "top_p": 1,
            "top_k": 1,
        },
    )

    try:
        text = response.text.strip()

        if text.startswith("```"):
            text = text.split("```")[1]

            if text.startswith("json"):
                text = text[4:]

        result = json.loads(text.strip())

    except json.JSONDecodeError:
        result = {}

    # 장소 후처리
    if category == "장소":
        for item in result.get("items", []):
            place_name = item.get("place_name")
            corrected_place_name = item.get("corrected_place_name")
            address = item.get("address")

            map_query = item.get("map_query") or corrected_place_name or place_name

            if not place_name:
                continue

            # 카카오 검색 후보
            search_queries = [place_name]

            if corrected_place_name and corrected_place_name != place_name:
                search_queries.append(corrected_place_name)

            if address:
                search_queries.append(address)

            kakao_place = None

            for query in search_queries:
                try:
                    print("카카오 검색:", query)

                    kakao = search_place(query)

                    if kakao.get("success") and kakao.get("places"):
                        kakao_place = kakao["places"][0]

                        print(
                            "카카오 검색 성공:",
                            kakao_place.get("place_name"),
                        )
                        break

                except Exception as e:
                    print(
                        "카카오 검색 오류:",
                        query,
                        repr(e),
                    )

            # 카카오에서 찾음
            if kakao_place:
                item["place_name"] = kakao_place.get(
                    "place_name",
                    corrected_place_name or place_name,
                )

                item["address"] = kakao_place["address"]
                item["latitude"] = kakao_place["latitude"]
                item["longitude"] = kakao_place["longitude"]
                item["map_url"] = kakao_place["place_url"]
                item["map_provider"] = "kakao"

            # 전부 실패 → Google Maps
            else:
                print(
                    "카카오 검색 실패 → Google:",
                    map_query,
                )

                item["map_url"] = build_google_map_url(map_query)
                item["map_provider"] = "google"

            # 내부 처리용 필드는 프론트에 반환하지 않음
            item.pop("corrected_place_name", None)
            item.pop("map_query", None)

    # 쇼핑 후처리
    elif category == "쇼핑":
        for item in result.get("items", []):
            product_name = item.get("product_name")
            brand_name = item.get("brand_name")

            search_query = item.get("search_query") or product_name

            # 네이버 쇼핑 검색
            if not search_query:
                item["shopping_url"] = None
            else:
                try:
                    item["shopping_url"] = search_shopping(search_query)
                except Exception:
                    item["shopping_url"] = None

            # 브랜드 검색
            if brand_name:
                item["brand_search_url"] = build_google_search_url(
                    f"{brand_name} instagram"
                )
            else:
                item["brand_search_url"] = None

            # 내부 처리용 필드 제거
            item.pop("search_query", None)
            item.pop("brand_name", None)

    # 일정 후처리
    elif category == "일정":
        for item in result.get("items", []):
            item["start_at"] = parse_dt(item.get("start_at"))

            item["end_at"] = parse_dt(item.get("end_at"))

    return result
