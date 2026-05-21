# Place 테이블 SQLAlchemy 모델 정의
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from app.core.database import Base

class Place(Base):
    __tablename__ = "place"

    place_id            = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id         = Column(Integer, ForeignKey("analysis_result.analysis_id", ondelete="CASCADE"), nullable=False)
    place_name          = Column(String(100), nullable=False)
    address             = Column(String(255), nullable=True)
    latitude            = Column(Float, nullable=True)
    longitude           = Column(Float, nullable=True)
    map_url             = Column(String(500), nullable=True)
    is_action_completed = Column(Boolean, nullable=False, default=False)