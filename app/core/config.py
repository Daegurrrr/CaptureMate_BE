# .env 환경변수 로드 및 설정 관리
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DB
    DATABASE_URL: str

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    S3_BUCKET_NAME: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60   # 만료 시간 60분
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60     # 60일동안 자동로그인 유지
    
     # Apple OAuth
    APPLE_BUNDLE_ID: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    class Config:
        env_file = ".env"

settings = Settings()

