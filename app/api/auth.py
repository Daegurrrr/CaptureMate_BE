# 인증 관련 API 엔드포인트

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.user import AppleLoginRequest, GoogleLoginRequest, TokenResponse, RegisterRequest, LoginRequest
from app.services.auth_service import apple_login, google_login, local_register, local_login, delete_account

router = APIRouter(prefix="/auth", tags=["auth"])


# 애플 로그인/회원가입
@router.post("/apple", response_model=TokenResponse)
async def apple_login_endpoint(
    request: AppleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await apple_login(request.identity_token, request.username, db)


# 구글 로그인/회원가입
@router.post("/google", response_model=TokenResponse)
async def google_login_endpoint(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await google_login(request.id_token, db)


# 로컬 회원가입
@router.post("/register", response_model=TokenResponse)
async def register_endpoint(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await local_register(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 로컬 로그인
@router.post("/login", response_model=TokenResponse)
async def login_endpoint(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await local_login(request, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# 로그아웃
@router.post("/logout")
async def logout_endpoint(
    current_user_id: int = Depends(get_current_user)
):
    return {"message": "로그아웃 되었습니다"}


# 회원탈퇴
@router.delete("/me")
async def withdraw_endpoint(
    current_user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        await delete_account(current_user_id, db)
        return {"message": "회원탈퇴 완료"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))