# .env 환경변수 로드 및 설정 관리
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
   
    # KaKaoMap
    KAKAOMAP_REST_API_KEY: str
    
    # Gemini
    GEMINI_API_KEY: str
    
    # Naver Search
    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

