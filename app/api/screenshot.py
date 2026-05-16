# 스크린샷 업로드 엔드포인트
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.s3_service import upload_image
from app.core.database import get_db
from app.models.screenshot import Screenshot
from app.models.analysis_result import AnalysisResult
from datetime import datetime
import uuid
import io
from app.ai.ocr import extract_text
from app.ai.classifier import final_classify_with_confidence
from datetime import datetime, timezone, timedelta
import os

KST = timezone(timedelta(hours=9))

router = APIRouter()

@router.post("/upload")
async def upload_screenshot(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # S3 업로드 + OCR + 분류 + DB 저장 (실제 운영용)

    # 파일 내용 먼저 읽어두기 (스트림 재사용을 위해)
    file_bytes = await file.read()

    # S3 업로드
    filename = f"{uuid.uuid4()}_{file.filename}"
    image_url = upload_image(io.BytesIO(file_bytes), filename)

    # 임시 파일로 OCR + 분류
    tmp_path = f"tmp_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    try:
        ocr_text = extract_text(tmp_path)
        category, confidence, level, _ = final_classify_with_confidence(ocr_text)
    finally:
        os.remove(tmp_path)

    screenshot_id = str(uuid.uuid4())[:24]

    # Screenshot 먼저 저장
    screenshot = Screenshot(
        screenshot_id = screenshot_id,
        user_id       = 1,
        image_url     = image_url,
        ocr_text      = ocr_text,
        status        = "done",
        created_at = datetime.now(KST).replace(tzinfo=None)
    )
    db.add(screenshot)
    await db.flush()  # screenshot_id FK 참조 가능하도록 먼저 flush

    # AnalysisResult 저장
    analysis = AnalysisResult(
        analysis_id      = str(uuid.uuid4())[:24],
        screenshot_id    = screenshot_id,
        category         = category,
        confidence_score = float(confidence),  # np.float64 → float 변환
    )
    db.add(analysis)
    await db.commit()

    return {
        "screenshot_id": screenshot_id,
        "url": image_url,
        "category": category,
        "confidence": round(float(confidence), 4),
        "confidence_level": level,
    }

@router.post("/ai")
async def analyze_screenshot(
    file: UploadFile = File(...)
):
    # OCR + 분류만 수행 (S3 저장 없음, DB 저장 없음 / 테스트용)
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