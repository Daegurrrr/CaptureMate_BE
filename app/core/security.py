# JWT 토큰 발급 및 검증

from datetime import datetime, timedelta
import jwt
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()

# user_id로 access token 생성 (만료 60분)
def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# user_id로 refresh token 생성 (만료 60일, 자동로그인 유지)
def create_refresh_token(user_id: int) -> str: 
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# 토큰 검증 및 payload 반환 (만료/위조 시 자동 에러)
def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# JWT에서 user_id 추출 (엔드포인트 인증용)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> int:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="access token이 아닙니다")
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")