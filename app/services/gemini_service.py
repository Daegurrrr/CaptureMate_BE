# Gemini를 활용한 카테고리별 필드 추출 서비스
from google import genai
import json
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def build_prompt(category: str, ocr_text: str) -> str:
    prompts = {
        "쇼핑": f"""당신은 쇼핑 스크린샷에서 정보를 추출하는 AI입니다.
아래 OCR 텍스트에서 상품명 목록을 추출하세요. 여러 상품이 있을 경우 모두 추출하세요.
반드시 JSON 형식으로만 응답하세요. 마크다운 없이 순수 JSON만 출력하세요.
추출할 수 없는 필드는 null로 설정하세요.

OCR 텍스트:
{ocr_text}

응답 형식:
{{"items": [{{"product_name": "..."}}]}}""",

        "장소": f"""당신은 장소 스크린샷에서 정보를 추출하는 AI입니다.
아래 OCR 텍스트에서 장소명과 주소 목록을 추출하세요. 여러 장소가 있을 경우 모두 추출하세요.
반드시 JSON 형식으로만 응답하세요. 마크다운 없이 순수 JSON만 출력하세요.
추출할 수 없는 필드는 null로 설정하세요.

OCR 텍스트:
{ocr_text}

응답 형식:
{{"items": [{{"place_name": "...", "address": "..."}}]}}""",

        "일정": f"""당신은 일정 스크린샷에서 정보를 추출하는 AI입니다.
아래 OCR 텍스트에서 일정 목록을 추출하세요. 여러 일정이 있을 경우 모두 추출하세요.
반드시 JSON 형식으로만 응답하세요. 마크다운 없이 순수 JSON만 출력하세요.
추출할 수 없는 필드는 null로 설정하세요.

OCR 텍스트:
{ocr_text}

응답 형식:
{{"items": [{{"title": "...", "start_at": "YYYY-MM-DDTHH:MM:SS", "end_at": "YYYY-MM-DDTHH:MM:SS"}}]}}""",

        "메모": f"""당신은 메모 스크린샷에서 정보를 추출하는 AI입니다.
아래 OCR 텍스트에서 제목과 핵심 내용을 요약하세요.
반드시 JSON 형식으로만 응답하세요. 마크다운 없이 순수 JSON만 출력하세요.
추출할 수 없는 필드는 null로 설정하세요.

OCR 텍스트:
{ocr_text}

응답 형식:
{{"title": "...", "content": "..."}}""",
    }
    return prompts.get(category, prompts["메모"])

async def analyze_with_gemini(category: str, ocr_text: str) -> dict:
    prompt = build_prompt(category, ocr_text)
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    try:
        result = json.loads(response.text.strip())
    except json.JSONDecodeError:
        result = {}
    
    return result