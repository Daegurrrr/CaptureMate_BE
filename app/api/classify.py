from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.classifier_model import predict_category

router = APIRouter(prefix="/classify", tags=["Classification"])


class ClassifyRequest(BaseModel):
    local_identifier: str
    ocr_text: str


@router.post("", summary="OCR 텍스트 분류")
async def classify(request: ClassifyRequest):
    result = predict_category(request.ocr_text)

    confidence = result["confidence"]

    confidence_level = (
        "높음"
        if confidence >= 0.8
        else "보통"
        if confidence >= 0.5
        else "낮음"
    )

    return {
        "local_identifier": request.local_identifier,
        "ocr_text": request.ocr_text,
        "category": result["category"],
        "confidence": round(float(confidence), 4),
        "confidence_level": confidence_level,
    }