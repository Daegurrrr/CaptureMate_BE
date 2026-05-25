# FastAPI 앱 생성, 라우터 등록, 서버 진입점
from fastapi import FastAPI
from app.api import place, auth, screenshot
from app.api import classify_model as ai

app = FastAPI(
    title="CaptureMate API",
    version="0.1.0"
)

app.include_router(ai.router, prefix = "/ai")  
app.include_router(screenshot.router, prefix="/screenshots")
app.include_router(place.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "CaptureMate API 서버 정상 작동 중"}