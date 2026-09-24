from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


class Mistake(Base):
    __tablename__ = "mistakes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    record_id = Column(String, nullable=True)   # 原始记录 id，record 删除后可为空
    subject = Column(String(20), nullable=False)
    note = Column(Text)                              # 错误原因摘要
    status = Column(String(10), default="pending")   # pending | mastered
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    mastered_at = Column(DateTime)
    # 独立存储批改内容，不依赖 record
    image_url = Column(Text)
    ai_feedback = Column(Text)
    output_schema = Column(String(20), default="simple")

    student = relationship("User", back_populates="mistakes")
