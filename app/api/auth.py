# 인증 관련 API 엔드포인트

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import AppleLoginRequest, TokenResponse
from app.services.auth_service import apple_login

router = APIRouter(prefix="/auth", tags=["auth"])

# 애플 로그인/회원가입
@router.post("/apple", response_model=TokenResponse)
async def apple_login_endpoint(
    request: AppleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await apple_login(request.identity_token, request.username, db)