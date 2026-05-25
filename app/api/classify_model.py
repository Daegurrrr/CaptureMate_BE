# app/api/classify_model.py

import json
import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.ai.classifier_model import predict_category
from app.ai.ocr import extract_text
from app.models.screenshot import Screenshot
from app.models.analysis_result import AnalysisResult
from app.models.place import Place
from app.models.schedule import Schedule
from app.models.shopping import Shopping
from app.models.memo import Memo
from app.services.gemini_service import analyze_with_gemini
from app.services.kakao_service import search_place
from app.services.naver_service import search_shopping
from datetime import datetime, timezone, timedelta
from fastapi import Form
import tempfile, os

KST = timezone(timedelta(hours=9))

router = APIRouter(tags=["ai"])


class ClassifyResponse(BaseModel):
    category: str
    confidence: float


def parse_dt(val):
    if val is None:
        return None
    try:
        return datetime.fromisoformat(val)
    except:
        return None


@router.post("/classify/model", response_model=ClassifyResponse, summary="채유니 모델")
async def classify_with_image(file: UploadFile = File(...)):
    with tempfile.NamedTemporementFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        ocr_text = extract_text(tmp_path)
        if not ocr_text:
            raise HTTPException(status_code=400, detail="OCR 결과가 없습니다")
        return predict_category(ocr_text)
    finally:
        os.remove(tmp_path)


@router.post("/classify/model/db", summary="채유니 모델 + DB 저장")
async def classify_with_image_and_save(
    file: UploadFile = File(...),
    local_identifier: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        ocr_text = extract_text(tmp_path)
        if not ocr_text:
            raise HTTPException(status_code=400, detail="OCR 결과가 없습니다")
        result = predict_category(ocr_text)
        category = result["category"]
        confidence = result["confidence"]
        level = "높음" if confidence >= 0.8 else "보통" if confidence >= 0.5 else "낮음"
    finally:
        os.remove(tmp_path)

    # 중복 체크
    existing = await db.execute(
        select(Screenshot).where(
            Screenshot.local_identifier == local_identifier,
            Screenshot.user_id == 1
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 처리된 스크린샷입니다")

    screenshot = Screenshot(
        user_id          = 1,
        local_identifier = local_identifier,
        ocr_text         = ocr_text,
        status           = "done",
        created_at       = datetime.now(KST).replace(tzinfo=None)
    )
    db.add(screenshot)
    await db.flush()

    gemini_result = await analyze_with_gemini(category, ocr_text)

    analysis = AnalysisResult(
        screenshot_id    = screenshot.screenshot_id,
        category         = category,
        confidence_score = float(confidence),
        summary          = json.dumps(gemini_result, ensure_ascii=False),
    )
    db.add(analysis)
    await db.flush()

    if category == "장소":
        for item in gemini_result.get("items", []):
            place_name = item.get("place_name") or "unknown"
            kakao = await asyncio.get_event_loop().run_in_executor(
                None, search_place, place_name
            )
            kakao_place = kakao.get("places", [{}])[0] if kakao.get("success") else {}
            db.add(Place(
                analysis_id = analysis.analysis_id,
                place_name  = place_name,
                address     = kakao_place.get("address") or item.get("address"),
                latitude    = kakao_place.get("latitude"),
                longitude   = kakao_place.get("longitude"),
                map_url     = kakao_place.get("place_url"),
            ))
    elif category == "일정":
        for item in gemini_result.get("items", []):
            db.add(Schedule(
                analysis_id = analysis.analysis_id,
                title       = item.get("title"),
                start_at    = parse_dt(item.get("start_at")),
                end_at      = parse_dt(item.get("end_at")),
            ))
    elif category == "쇼핑":
        for item in gemini_result.get("items", []):
            product_name = item.get("product_name")
            shopping_url = search_shopping(product_name) if product_name else None
            db.add(Shopping(
                analysis_id  = analysis.analysis_id,
                product_name = product_name,
                shopping_url = shopping_url,
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