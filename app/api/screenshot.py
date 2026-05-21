# 스크린샷 업로드 엔드포인트
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.screenshot import Screenshot
from app.models.analysis_result import AnalysisResult
from app.models.place import Place
from app.models.schedule import Schedule
from app.models.shopping import Shopping
from app.models.memo import Memo
from app.services.gemini_service import analyze_with_gemini
from datetime import datetime, timezone, timedelta
import os
from app.ai.ocr import extract_text
from app.ai.classifier import final_classify_with_confidence

KST = timezone(timedelta(hours=9))

router = APIRouter()

def parse_dt(val):
    if val is None:
        return None
    try:
        return datetime.fromisoformat(val)
    except:
        return None

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
        os.remove(tmp_path)

    # Screenshot 저장 (local_identifier로 기기 내 사진 식별)
    screenshot = Screenshot(
        user_id          = 1,  # 추후 JWT 미들웨어로 교체
        local_identifier = local_identifier,
        ocr_text         = ocr_text,
        status           = "done",
        created_at       = datetime.now(KST).replace(tzinfo=None)
    )
    db.add(screenshot)
    await db.flush()  

    analysis = AnalysisResult(
        screenshot_id    = screenshot.screenshot_id,
        category         = category,
        confidence_score = float(confidence), 
    )
    db.add(analysis)
    await db.flush() 

    # Gemini 프롬프팅으로 카테고리별 필드 추출
    gemini_result = await analyze_with_gemini(category, ocr_text)

    # 카테고리별 테이블 저장
    if category == "장소":
        db.add(Place(
            analysis_id = analysis.analysis_id,
            place_name  = gemini_result.get("place_name") or "unknown",
            address     = gemini_result.get("address"),
        ))
    elif category == "일정":
        db.add(Schedule(
            analysis_id = analysis.analysis_id,
            title       = gemini_result.get("title"),
            start_at    = parse_dt(gemini_result.get("start_at")),  
            end_at      = parse_dt(gemini_result.get("end_at")),  
        ))
    elif category == "쇼핑":
        db.add(Shopping(
            analysis_id  = analysis.analysis_id,
            product_name = gemini_result.get("product_name"),
        ))
    elif category in ("메모", "기타"):
        db.add(Memo(
            analysis_id = analysis.analysis_id,
            title       = gemini_result.get("title"),
            content     = gemini_result.get("content"),
        ))

    await db.commit()

    return {
        "screenshot_id": screenshot.screenshot_id,
        "category": category,
        "confidence": round(float(confidence), 4),
        "confidence_level": level,
        "gemini_result": gemini_result,
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