from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)  # 登录账号
    password_hash = Column(String(200), nullable=False)
    name = Column(String(50))                                    # 显示名
    role = Column(String(10), default="student")                 # student | admin
    grade_level = Column(String(10))                             # junior | senior
    is_active = Column(Boolean, default=True)
    session_token = Column(Text)                                 # 当前有效token，单设备互踢
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)

    subscriptions = relationship("Subscription", back_populates="student")
    records = relationship("Record", back_populates="student")
    mistakes = relationship("Mistake", back_populates="student")
