from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


class Record(Base):
    __tablename__ = "records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String(20), nullable=False)
    exercise_type_id = Column(String, ForeignKey("exercise_types.id"), nullable=True)
    image_url = Column(String(500), nullable=False)   # OSS 图片地址
    is_correct = Column(Boolean)                       # 批改结论
    ai_feedback = Column(Text)                         # AI 批改内容（JSON）
    ai_thinking = Column(Text)                         # AI 解题思路（懒加载）
    token_input = Column(Integer, default=0)
    token_output = Column(Integer, default=0)
    llm_provider = Column(String(50))                  # 记录当时用的哪个LLM
    llm_model = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", back_populates="records")
    exercise_type = relationship("ExerciseType", back_populates="records")
