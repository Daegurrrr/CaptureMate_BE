# .env 환경변수 로드 및 설정 관리

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
    
    # KaKaoMap
    KAKAO_REST_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()