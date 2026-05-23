from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.place import Place
from app.models.analysis_result import AnalysisResult
from app.services.kakao_service import search_place

router = APIRouter(tags=["Places"])

# 1. 장소 목록 조회
@router.get("/analysis/{analysis_id}/places", summary="장소 목록 조회")
async def get_places(
    analysis_id: int,
    db: AsyncSession = Depends(get_db)
):
    analysis = await db.execute(
        select(AnalysisResult).where(AnalysisResult.analysis_id == analysis_id)
    )
    if not analysis.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="존재하지 않는 분석 ID")

    result = await db.execute(
        select(Place).where(Place.analysis_id == analysis_id)
    )
    places = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "place_id": p.place_id,
                "place_name": p.place_name,
                "address": p.address,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "map_url": p.map_url,
                "is_action_completed": p.is_action_completed,
            }
            for p in places
        ]
    }


# 2. 장소 상세 조회
@router.get("/places/{place_id}", summary="장소 상세 조회")
async def get_place(
    place_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Place).where(Place.place_id == place_id)
    )
    place = result.scalar_one_or_none()

    if not place:
        raise HTTPException(status_code=404, detail="존재하지 않는 장소 ID")

    return {
        "success": True,
        "data": {
            "place_id": place.place_id,
            "place_name": place.place_name,
            "address": place.address,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "map_url": place.map_url,
            "is_action_completed": place.is_action_completed,
        }
    }


# 3. 추천액션 완료 처리
@router.patch("/places/{place_id}/action", summary="추천액션 완료 처리")
async def complete_action(
    place_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Place).where(Place.place_id == place_id)
    )
    place = result.scalar_one_or_none()

    if not place:
        raise HTTPException(status_code=404, detail="존재하지 않는 장소 ID")

    place.is_action_completed = True
    await db.commit()

    return {
        "success": True,
        "is_action_completed": True,
        "message": "완료 처리되었습니다."
    }