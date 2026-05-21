# Shopping 테이블 SQLAlchemy 모델 정의
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.core.database import Base

class Shopping(Base):
    __tablename__ = "shopping"

    shopping_id         = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id         = Column(Integer, ForeignKey("analysis_result.analysis_id", ondelete="CASCADE"), nullable=False)
    product_name        = Column(String(255), nullable=True)
    shopping_url        = Column(String(500), nullable=True)
    is_action_completed = Column(Boolean, nullable=False, default=False)