import json
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
from app.ai.classifier_model import predict_category  # 허깅페이스 모델로 교체 (기존 classifier.py 제거)
from app.services.kakao_service import search_place
from app.services.naver_service import search_shopping

KST = timezone(timedelta(hours=9))

router = APIRouter(tags=["Screenshots"])

def parse_dt(val):
    if val is None:
        return None
    try:
        return datetime.fromisoformat(val)
    except:
        return None

@router.post("", summary="스크린샷 업로드")
async def upload_screenshot(
    file: UploadFile = File(...),
    local_identifier: str = Form(...),
    # model 파라미터 제거 (허깅페이스 모델로 단일화)
    db: AsyncSession = Depends(get_db)
):
    # 중복 체크
    existing = await db.execute(
        select(Screenshot).where(
            Screenshot.local_identifier == local_identifier,
            Screenshot.user_id == 1
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 처리된 스크린샷입니다")

    file_bytes = await file.read()

    tmp_path = f"tmp_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    try:
        ocr_text = extract_text(tmp_path)
        # 허깅페이스 모델로 분류 (기존 final_classify_with_confidence 제거)
        result = predict_category(ocr_text)
        category = result["category"]
        confidence = result["confidence"]
        level = "높음" if confidence >= 0.8 else "보통" if confidence >= 0.5 else "낮음"
    finally:
        os.remove(tmp_path)

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

@router.post("/ai", summary="OCR 및 분류 테스트")
async def analyze_screenshot(
    file: UploadFile = File(...)
):
    tmp_path = f"tmp_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    try:
        text = extract_text(tmp_path)
        # 허깅페이스 모델로 교체
        result = predict_category(text)
        return {
            "ocr_text": text,
            "category": result["category"],
            "confidence": result["confidence"],
            "confidence_level": "높음" if result["confidence"] >= 0.8 else "보통" if result["confidence"] >= 0.5 else "낮음",
        }
    finally:
        os.remove(tmp_path)

@router.get("", summary="스크린샷 목록 조회")
async def get_screenshots(
    status: str = None,
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    query = select(Screenshot).where(Screenshot.user_id == 1)

    if status:
        query = query.where(Screenshot.status == status)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(Screenshot.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    screenshots = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "screenshot_id": s.screenshot_id,
                "local_identifier": s.local_identifier,
                "status": s.status,
                "created_at": s.created_at,
            }
            for s in screenshots
        ],
        "total": total,
        "page": page,
    }

@router.get("/detail", summary="스크린샷 상세 조회")
async def get_screenshot(
    local_identifier: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Screenshot).where(
            Screenshot.local_identifier == local_identifier,
            Screenshot.user_id == 1
        )
    )
    screenshot = result.scalar_one_or_none()

    if not screenshot:
        raise HTTPException(status_code=404, detail="존재하지 않는 스크린샷")

    analysis_result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.screenshot_id == screenshot.screenshot_id)
    )
    analysis = analysis_result.scalar_one_or_none()

    items = []
    if analysis:
        if analysis.category == "장소":
            places_result = await db.execute(
                select(Place).where(Place.analysis_id == analysis.analysis_id)
            )
            items = [
                {
                    "place_id": p.place_id,
                    "place_name": p.place_name,
                    "address": p.address,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "map_url": p.map_url,
                    "is_action_completed": p.is_action_completed,
                }
                for p in places_result.scalars().all()
            ]
        elif analysis.category == "일정":
            schedules_result = await db.execute(
                select(Schedule).where(Schedule.analysis_id == analysis.analysis_id)
            )
            items = [
                {
                    "schedule_id": s.schedule_id,
                    "title": s.title,
                    "start_at": s.start_at,
                    "end_at": s.end_at,
                    "is_action_completed": s.is_action_completed,
                }
                for s in schedules_result.scalars().all()
            ]
        elif analysis.category == "쇼핑":
            shoppings_result = await db.execute(
                select(Shopping).where(Shopping.analysis_id == analysis.analysis_id)
            )
            items = [
                {
                    "shopping_id": s.shopping_id,
                    "product_name": s.product_name,
                    "shopping_url": s.shopping_url,
                    "is_action_completed": s.is_action_completed,
                }
                for s in shoppings_result.scalars().all()
            ]
        elif analysis.category in ("메모", "기타"):
            memos_result = await db.execute(
                select(Memo).where(Memo.analysis_id == analysis.analysis_id)
            )
            items = [
                {
                    "memo_id": m.memo_id,
                    "title": m.title,
                    "content": m.content,
                }
                for m in memos_result.scalars().all()
            ]

    return {
        "success": True,
        "data": {
            "screenshot_id": screenshot.screenshot_id,
            "local_identifier": screenshot.local_identifier,
            "ocr_text": screenshot.ocr_text,
            "status": screenshot.status,
            "created_at": screenshot.created_at,
            "analysis": {
                "analysis_id": analysis.analysis_id,
                "category": analysis.category,
                "confidence_score": analysis.confidence_score,
                "analyzed_at": analysis.analyzed_at,
                "items": items,
            } if analysis else None
        }
    }