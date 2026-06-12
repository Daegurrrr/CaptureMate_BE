# AnalysisResult 테이블 SQLAlchemy 모델 정의
from sqlalchemy import Column, Integer, String, Float, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime, timezone, timedelta
KST = timezone(timedelta(hours=9))

class AnalysisResult(Base):
    __tablename__ = "analysis_result"

    analysis_id      = Column(Integer, primary_key=True, autoincrement=True)
    screenshot_id    = Column(Integer, ForeignKey("screenshot.screenshot_id", ondelete="CASCADE"), nullable=False)
    category         = Column(String(10), nullable=False)
    confidence_score = Column(Float, nullable=False)
    summary          = Column(Text, nullable=True)
    analyzed_at = Column(TIMESTAMP, default=lambda: datetime.now(KST).replace(tzinfo=None))