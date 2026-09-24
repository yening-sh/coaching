from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String(20), nullable=False)   # math|chinese|english|physics|chemistry|biology
    grade_level = Column(String(10), nullable=False)  # junior | senior
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    note = Column(String(200))                     # 备注，如"管理员手动开通"

    student = relationship("User", back_populates="subscriptions")
