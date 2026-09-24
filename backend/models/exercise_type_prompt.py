from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


class ExerciseTypePrompt(Base):
    __tablename__ = "exercise_type_prompts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_type_id = Column(String, ForeignKey("exercise_types.id"), nullable=False)
    version_name = Column(String(100), nullable=False)   # 如 "v1 初版"
    prompt_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=False)           # 同一题型只有一个激活
    created_at = Column(DateTime, default=datetime.utcnow)

    exercise_type = relationship("ExerciseType", back_populates="prompts")
