# Screenshot 테이블 SQLAlchemy 모델 정의
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, UniqueConstraint
from app.core.database import Base

class Screenshot(Base):
    __tablename__ = "screenshot"

    screenshot_id    = Column(String(26), primary_key=True)
    user_id          = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    local_identifier = Column(String(255), nullable=False)
    ocr_text         = Column(Text, nullable=True)
    status           = Column(String(10), nullable=False, default='pending')
    created_at       = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'local_identifier', name='uq_user_local'),
    )