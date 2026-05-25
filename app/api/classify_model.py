# app/api/classify_model.py

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from app.ai.classifier_model import predict_category
from app.ai.ocr import extract_text
import tempfile, os

router = APIRouter(tags=["ai"])


class ClassifyResponse(BaseModel):
    category: str
    confidence: float


@router.post("/classify/model", response_model=ClassifyResponse, summary = "채유니 모델")
async def classify_with_image(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        ocr_text = extract_text(tmp_path)
        if not ocr_text:
            raise HTTPException(status_code=400, detail="OCR 결과가 없습니다")
        return predict_category(ocr_text)
    finally:
        os.remove(tmp_path)