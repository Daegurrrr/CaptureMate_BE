# 로그인/회원가입 비즈니스 로직, 애플로그인

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings

APPLE_PUBLIC_KEY_URL = "https://appleid.apple.com/auth/keys"

# 애플 공개키로 identity_token 검증 후 payload 반환
async def verify_apple_token(identity_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(APPLE_PUBLIC_KEY_URL)
        apple_keys = response.json()["keys"]

    # 토큰 헤더에서 kid 추출 (어떤 키로 서명됐는지)
    header = jwt.get_unverified_header(identity_token)
    kid = header["kid"]

    # 매칭되는 공개키 찾기
    public_key = None
    for key in apple_keys:
        if key["kid"] == kid:
            public_key = RSAAlgorithm.from_jwk(key)
            break

    if not public_key:
        raise ValueError("매칭되는 애플 공개키 없음")

    # 토큰 검증 및 payload 반환
    payload = jwt.decode(
        identity_token,
        public_key,
        algorithms=["RS256"],
        audience=settings.APPLE_BUNDLE_ID  # .env에서 관리
    )
    return payload

# 애플 로그인 처리: 신규면 가입, 기존이면 조회 후 JWT 발급
async def apple_login(identity_token: str, username: str | None, db: AsyncSession) -> dict:
    payload = await verify_apple_token(identity_token)
    social_id = payload["sub"]  # 애플 고유 유저 ID

    # 기존 유저 조회
    result = await db.execute(select(User).where(User.social_id == social_id))
    user = result.scalar_one_or_none()

    # 신규 유저면 생성
    if not user:
        user = User(
            auth_provider="apple",
            social_id=social_id,
            username=username or "애플유저",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return {
        "access_token": create_access_token(user.user_id),
        "refresh_token": create_refresh_token(user.user_id),
        "token_type": "bearer"
    }