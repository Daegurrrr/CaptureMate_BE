# FastAPI 앱 생성, 라우터 등록, 서버 진입점
from fastapi import FastAPI
from app.api import screenshot
from app.api import place

app = FastAPI(
    title="CaptureMate API",
    version="0.1.0"
)

app.include_router(screenshot.router, prefix="/screenshot")
app.include_router(
    place.router,
    prefix="/places"
)


@app.get("/")
async def root():
    return {"message": "CaptureMate API 서버 정상 작동 중"}