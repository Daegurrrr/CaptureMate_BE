# Memo 테이블 SQLAlchemy 모델 정의
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.core.database import Base

class Memo(Base):
    __tablename__ = "memo"

    memo_id     = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analysis_result.analysis_id", ondelete="CASCADE"), nullable=False)
    title       = Column(String(255), nullable=True)
    content     = Column(Text, nullable=True)