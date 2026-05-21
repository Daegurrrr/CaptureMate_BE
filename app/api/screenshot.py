# 스크린샷 업로드 엔드포인트
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.screenshot import Screenshot
from app.models.analysis_result import AnalysisResult
from datetime import datetime, timezone, timedelta
import uuid
import os
from app.ai.ocr import extract_text
from app.ai.classifier import final_classify_with_confidence

KST = timezone(timedelta(hours=9))

router = APIRouter()

@router.post("/upload")
async def upload_screenshot(
    file: UploadFile = File(...),           # iOS에서 전송한 원본 이미지
    local_identifier: str = Form(...),      # iOS PhotoKit 로컬 식별자
    db: AsyncSession = Depends(get_db)
):
    file_bytes = await file.read()

    # OCR 처리를 위해 임시 파일로 저장
    tmp_path = f"tmp_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    try:
        # OCR 텍스트 추출
        ocr_text = extract_text(tmp_path)
        # KoBERT 분류 (카테고리, 신뢰도, 신뢰도 레벨)
        category, confidence, level, _ = final_classify_with_confidence(ocr_text)
    finally:
        # 처리 완료 후 임시 파일 삭제
        os.remove(tmp_path)

    screenshot_id = str(uuid.uuid4())[:24]

    # Screenshot 저장 (local_identifier로 기기 내 사진 식별)
    screenshot = Screenshot(
        screenshot_id    = screenshot_id,
        user_id          = 1,  # 추후 JWT 미들웨어로 교체
        local_identifier = local_identifier,
        ocr_text         = ocr_text,
        status           = "done",
        created_at       = datetime.now(KST).replace(tzinfo=None)
    )
    db.add(screenshot)
    await db.flush()  

    # AnalysisResult 저장
    analysis = AnalysisResult(
        analysis_id      = str(uuid.uuid4())[:24],
        screenshot_id    = screenshot_id,
        category         = category,
        confidence_score = float(confidence),
    )
    db.add(analysis)
    await db.commit()

    return {
        "screenshot_id": screenshot_id,
        "category": category,
        "confidence": round(float(confidence), 4),
        "confidence_level": level,
    }

@router.post("/ai")
async def analyze_screenshot(
    file: UploadFile = File(...)
):
    # OCR + 분류만 수행 (DB 저장 없음 / 테스트용)
    tmp_path = f"tmp_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    try:
        text = extract_text(tmp_path)
        category, confidence, level, probs = final_classify_with_confidence(text)
        return {
            "ocr_text": text,
            "category": category,
            "confidence": round(confidence, 4),
            "confidence_level": level,
        }
    finally:
        os.remove(tmp_path)