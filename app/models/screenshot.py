# Screenshot 테이블 SQLAlchemy 모델 정의
from sqlalchemy import Column, String, Text, DateTime
from app.core.database import Base

class Screenshot(Base):
    __tablename__ = "Screenshot"

    screenshot_id = Column(String(24), primary_key=True)
    user_id       = Column(String(24), nullable=False)
    image_url     = Column(String(500), nullable=False)
    ocr_text      = Column(Text, nullable=True)
    status        = Column(String(10), nullable=False, default='pending')
    captured_at   = Column(DateTime, nullable=True)
    created_at    = Column(DateTime, nullable=False)