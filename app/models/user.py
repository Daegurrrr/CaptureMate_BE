# User 테이블 SQLAlchemy 모델 정의

from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    user_id              = Column(Integer, primary_key=True, autoincrement=True)
    login_id             = Column(String(50), unique=True, nullable=True)
    password             = Column(String(255), nullable=True)
    auth_provider        = Column(String(10), nullable=False)
    social_id            = Column(String(100), unique=True, nullable=True)
    username             = Column(String(50), nullable=False)
    email                = Column(String(255), unique=True, nullable=True)
    device_token         = Column(String(255), nullable=True)
    notification_enabled = Column(Boolean, nullable=False, default=True)
    created_at           = Column(TIMESTAMP, nullable=False, server_default=func.now())