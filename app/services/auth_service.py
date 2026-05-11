# 로그인/회원가입 비즈니스 로직

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import RegisterRequest, LoginRequest
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings

APPLE_PUBLIC_KEY_URL = "https://appleid.apple.com/auth/keys"
GOOGLE_TOKEN_VERIFY_URL = "https://oauth2.googleapis.com/tokeninfo"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── 로컬 ──────────────────────────────────────────────

async def local_register(data: RegisterRequest, db: AsyncSession) -> dict:
    # login_id 중복 체크
    result = await db.execute(select(User).where(User.login_id == data.login_id))
    if result.scalar_one_or_none():
        raise ValueError("이미 사용 중인 아이디입니다")

    # email 중복 체크
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise ValueError("이미 사용 중인 이메일입니다")

    user = User(
        auth_provider="local",
        login_id=data.login_id,
        password=pwd_context.hash(data.password),
        username=data.username,
        email=data.email,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "access_token": create_access_token(user.user_id),
        "refresh_token": create_refresh_token(user.user_id),
        "token_type": "bearer"
    }


async def local_login(data: LoginRequest, db: AsyncSession) -> dict:
    result = await db.execute(select(User).where(User.login_id == data.login_id))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.password):
        raise ValueError("아이디 또는 비밀번호가 올바르지 않습니다")

    return {
        "access_token": create_access_token(user.user_id),
        "refresh_token": create_refresh_token(user.user_id),
        "token_type": "bearer"
    }


async def delete_account(user_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("유저 없음")

    if user.auth_provider == "google" and user.social_id:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": user.social_id}
            )

    await db.delete(user)
    await db.commit()


# ── 애플 ──────────────────────────────────────────────

async def verify_apple_token(identity_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(APPLE_PUBLIC_KEY_URL)
        apple_keys = response.json()["keys"]

    header = jwt.get_unverified_header(identity_token)
    kid = header["kid"]

    public_key = None
    for key in apple_keys:
        if key["kid"] == kid:
            public_key = RSAAlgorithm.from_jwk(key)
            break

    if not public_key:
        raise ValueError("매칭되는 애플 공개키 없음")

    payload = jwt.decode(
        identity_token,
        public_key,
        algorithms=["RS256"],
        audience=settings.APPLE_BUNDLE_ID
    )
    return payload


async def apple_login(identity_token: str, username: str | None, db: AsyncSession) -> dict:
    payload = await verify_apple_token(identity_token)
    social_id = payload["sub"]

    result = await db.execute(select(User).where(User.social_id == social_id))
    user = result.scalar_one_or_none()

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


# ── 구글 ──────────────────────────────────────────────

async def verify_google_token(id_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_TOKEN_VERIFY_URL,
            params={"id_token": id_token}
        )
    if response.status_code != 200:
        raise ValueError("유효하지 않은 구글 토큰")

    return response.json()


async def google_login(id_token: str, db: AsyncSession) -> dict:
    payload = await verify_google_token(id_token)
    social_id = payload["sub"]
    username = payload.get("name") or payload.get("email", "구글유저")

    result = await db.execute(select(User).where(User.social_id == social_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            auth_provider="google",
            social_id=social_id,
            username=username,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return {
        "access_token": create_access_token(user.user_id),
        "refresh_token": create_refresh_token(user.user_id),
        "token_type": "bearer"
    }
    
    # ── 카카오 ──────────────────────────────────────────────

KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

async def kakao_login(access_token: str, db: AsyncSession) -> dict:
    # 카카오 유저 정보 조회
    async with httpx.AsyncClient() as client:
        response = await client.get(
            KAKAO_USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
    if response.status_code != 200:
        raise ValueError("유효하지 않은 카카오 토큰")

    payload = response.json()
    social_id = str(payload["id"])
    kakao_account = payload.get("kakao_account", {})
    username = kakao_account.get("profile", {}).get("nickname", "카카오유저")

    # 기존 유저 조회
    result = await db.execute(select(User).where(User.social_id == social_id))
    user = result.scalar_one_or_none()

    # 신규 유저면 생성
    if not user:
        user = User(
            auth_provider="kakao",
            social_id=social_id,
            username=username,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return {
        "access_token": create_access_token(user.user_id),
        "refresh_token": create_refresh_token(user.user_id),
        "token_type": "bearer"
    }