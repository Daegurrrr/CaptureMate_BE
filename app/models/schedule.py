# Schedule 테이블 SQLAlchemy 모델 정의
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.core.database import Base

class Schedule(Base):
    __tablename__ = "schedule"

    schedule_id         = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id         = Column(Integer, ForeignKey("analysis_result.analysis_id", ondelete="CASCADE"), nullable=False)
    title               = Column(String(255), nullable=True)
    start_at            = Column(DateTime, nullable=True)
    end_at              = Column(DateTime, nullable=True)
    is_action_completed = Column(Boolean, nullable=False, default=False)