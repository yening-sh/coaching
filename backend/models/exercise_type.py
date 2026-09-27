from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from database import Base


class ExerciseType(Base):
    __tablename__ = "exercise_types"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(String(20), nullable=False)   # math|english|...
    name = Column(String(50), nullable=False)       # 如"英语翻译题"
    prompt_template = Column(Text, nullable=False)  # 含 {grade} {subject} 占位符
    # output_schema 描述期望的 JSON 结构，供前端渲染判断
    # "translation" → 数组，每条含 number/original/student_answer/is_correct/feedback/corrected
    # "essay"       → 作文批改 {score, overall, sentences, ...}
    # "grammar"     → 语法填空 {total_score, full_score, blanks, ...}
    # "math"        → 数学解答题 {is_correct, feedback, hint}
    # "summary"     → 概要写作 {is_correct, feedback, ...}
    output_schema = Column(String(20), default="math")
    is_active = Column(Boolean, default=True)
    sort_order = Column(String(5), default="0")    # 排序
    created_at = Column(DateTime, default=datetime.utcnow)

    records = relationship("Record", back_populates="exercise_type")
    prompts = relationship("ExerciseTypePrompt", back_populates="exercise_type", order_by="ExerciseTypePrompt.created_at")
