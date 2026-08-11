from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os

from app.ai.ocr import extract_text

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("", summary="OCR 추출")
async def extract_ocr(
    file: UploadFile = File(...),
    local_identifier: str = Form(...)
):
    file_bytes = await file.read()

    tmp_path = f"tmp_{file.filename}"

    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    try:
        ocr_text = extract_text(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return {
        "local_identifier": local_identifier,
        "ocr_text": ocr_text
    }