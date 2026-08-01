from fastapi import APIRouter
from pydantic import BaseModel

from app.services.gemini_service import analyze_with_gemini

router = APIRouter(prefix="/gemini", tags=["Gemini"])


class GeminiRequest(BaseModel):
    local_identifier: str
    ocr_text: str
    category: str


@router.post("", summary="Gemini 분석")
async def analyze(request: GeminiRequest):
    result = await analyze_with_gemini(
        category=request.category,
        ocr_text=request.ocr_text
    )

    return {
        "local_identifier": request.local_identifier,
        "category": request.category,
        "result": result
    }