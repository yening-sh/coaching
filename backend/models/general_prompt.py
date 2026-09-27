import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, UniqueConstraint
from database import Base


class GeneralPrompt(Base):
    __tablename__ = "general_prompts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    subject = Column(String(20), nullable=False)       # "english", "math", ...
    grade_level = Column(String(20), nullable=False)   # "senior", "junior", "all"
    prompt_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("subject", "grade_level", name="uq_general_prompt_subject_grade"),)
