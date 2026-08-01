from fastapi import FastAPI
from app.api import ocr, classify, gemini, place

app = FastAPI(
    title="CaptureMate API",
    version="0.1.0"
)

# API Router
app.include_router(ocr.router)
app.include_router(classify.router)
app.include_router(gemini.router)
app.include_router(place.router)


@app.get("/")
async def root():
    return {"message": "CaptureMate API 서버 정상 작동 중"}