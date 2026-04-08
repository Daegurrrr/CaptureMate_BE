# 스크린샷 업로드, 목록 조회 엔드포인트
# 스크린샷 업로드 엔드포인트
from fastapi import APIRouter, UploadFile, File
from app.services.s3_service import upload_image
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_screenshot(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}_{file.filename}"
    url = upload_image(file.file, filename)
    return {"url": url}