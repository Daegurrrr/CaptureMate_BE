# 인증 관련 API 엔드포인트

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import AppleLoginRequest, GoogleLoginRequest, KakaoLoginRequest, TokenResponse, RegisterRequest, LoginRequest
from app.services.auth_service import apple_login, google_login, kakao_login, local_register, local_login, delete_account
from app.core.security import get_current_user, create_access_token, decode_token, bearer_scheme
from fastapi.security import HTTPAuthorizationCredentials
import jwt

router = APIRouter(prefix="/auth", tags=["Auth"])


# 애플 로그인/회원가입
@router.post("/apple", response_model=TokenResponse, summary="애플 로그인/회원가입")
async def apple_login_endpoint(
    request: AppleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await apple_login(request.identity_token, request.username, db)


# 구글 로그인/회원가입
@router.post("/google", response_model=TokenResponse, summary="구글 로그인/회원가입")
async def google_login_endpoint(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    return await google_login(request.id_token, db)


# 카카오 로그인/회원가입
@router.post("/kakao", response_model=TokenResponse, summary="카카오 로그인/회원가입")
async def kakao_login_endpoint(
    request: KakaoLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await kakao_login(request.access_token, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# 로컬 회원가입
@router.post("/register", response_model=TokenResponse, summary="로컬 회원가입")
async def register_endpoint(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await local_register(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# 로컬 로그인
@router.post("/login", response_model=TokenResponse, summary="로컬 로그인")
async def login_endpoint(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await local_login(request, db)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# 로그아웃
@router.post("/logout", summary="로그아웃")
async def logout_endpoint(
    current_user_id: int = Depends(get_current_user)
):
    return {"message": "로그아웃 되었습니다"}


# 회원탈퇴
@router.delete("/me", summary="회원 탈퇴")
async def withdraw_endpoint(
    current_user_id: int = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        await delete_account(current_user_id, db)
        return {"message": "회원탈퇴 완료"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    


# access token 재발급
@router.post("/refresh", summary="액세스 토큰 재발급")
async def refresh_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="refresh token이 아닙니다")
        user_id = int(payload["sub"])
        new_access_token = create_access_token(user_id)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="refresh token이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")