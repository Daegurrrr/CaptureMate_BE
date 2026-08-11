from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os

from app.ai.ocr import extract_text
from app.ai.multimodal_classifier import predict_category


router = APIRouter(prefix="/classify", tags=["Classification"])


@router.post("", summary="OCR + 멀티모달 카테고리 분류")
async def classify(
    file: UploadFile = File(...),
    local_identifier: str = Form(...)
):
    file_bytes = await file.read()

    tmp_path = f"tmp_{file.filename}"

    try:
        # PaddleOCR용 임시 파일 저장
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        # 1. OCR
        ocr_text = extract_text(tmp_path)

        # 2. RoBERTa + CLIP 분류
        result = predict_category(
            ocr_text=ocr_text,
            image_bytes=file_bytes,
        )

        confidence = result["confidence"]

        confidence_level = (
            "높음"
            if confidence >= 0.8
            else "보통"
            if confidence >= 0.5
            else "낮음"
        )

        return {
            "local_identifier": local_identifier,
            "ocr_text": ocr_text,
            "category": result["category"],
            "confidence": round(float(confidence), 4),
            "confidence_level": confidence_level,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)