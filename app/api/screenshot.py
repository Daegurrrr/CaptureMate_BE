# 스크린샷 업로드 엔드포인트
import json
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
from app.ai.classifier import final_classify_with_confidence, confidence_level
from app.services.kakao_service import search_place

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

    # Gemini 프롬프팅으로 카테고리별 필드 추출
    gemini_result = await analyze_with_gemini(category, ocr_text)

    analysis = AnalysisResult(
        screenshot_id    = screenshot.screenshot_id,
        category         = category,
        confidence_score = float(confidence), 
        summary          = json.dumps(gemini_result, ensure_ascii=False), 
    )
    db.add(analysis)
    await db.flush() 

    # 카테고리별 테이블 저장
    if category == "장소":
        for item in gemini_result.get("items", []):
            place_name = item.get("place_name") or "unknown"
        
            kakao = search_place(place_name)
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
            db.add(Shopping(
                analysis_id  = analysis.analysis_id,
                product_name = item.get("product_name"),
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

# 스크린샷 목록 조회 엔드포인트
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

    # 전체 개수
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    # 페이지네이션
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
    
# 스크린샷 상세 조회 엔드포인트
@router.get("/{screenshot_id}", summary="스크린샷 상세 조회")
async def get_screenshot(
    screenshot_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Screenshot).where(Screenshot.screenshot_id == screenshot_id)
    )
    screenshot = result.scalar_one_or_none()

    if not screenshot:
        raise HTTPException(status_code=404, detail="존재하지 않는 캡처 ID")

    analysis_result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.screenshot_id == screenshot_id)
    )
    analysis = analysis_result.scalar_one_or_none()

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
                "summary": json.loads(analysis.summary) if analysis.summary else None,
                "analyzed_at": analysis.analyzed_at,
            } if analysis else None
        }
    }