# 스크린샷 업로드 엔드포인트
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.s3_service import upload_image
from app.core.database import get_db
from app.models.screenshot import Screenshot
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_screenshot(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    # S3 업로드
    filename = f"{uuid.uuid4()}_{file.filename}"
    image_url = upload_image(file.file, filename)

    # DB 저장
    screenshot = Screenshot(
        screenshot_id = str(uuid.uuid4())[:24],
        user_id       = 1,
        image_url     = image_url,
        status        = "pending",
        created_at    = datetime.utcnow()
    )
    db.add(screenshot)
    await db.commit()

    return {"screenshot_id": screenshot.screenshot_id, "url": image_url}