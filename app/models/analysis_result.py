# AnalysisResult 테이블 SQLAlchemy 모델 정의

from sqlalchemy import Column, String, Float, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_result"

    analysis_id       = Column(String(26), primary_key=True)
    screenshot_id     = Column(String(26), ForeignKey("screenshot.screenshot_id"), nullable=False)
    category          = Column(String(10), nullable=False)
    sub_category      = Column(String(50), nullable=True)
    confidence_score  = Column(Float, nullable=False)
    summary           = Column(Text, nullable=True)
    is_user_corrected = Column(Boolean, nullable=False, default=False)
    analyzed_at       = Column(TIMESTAMP, server_default=func.now())