# User 요청/응답 스키마
from pydantic import BaseModel, EmailStr

class AppleLoginRequest(BaseModel):
    identity_token: str
    username: str | None = None  # 애플은 최초 로그인 시에만 이름 제공

class GoogleLoginRequest(BaseModel):
    id_token: str  # 구글에서 받은 id_token
    
class KakaoLoginRequest(BaseModel):
    access_token: str
    
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
class RegisterRequest(BaseModel):
    login_id: str
    password: str
    username: str
    email: EmailStr

class LoginRequest(BaseModel):
    login_id: str
    password: str
