from sqlalchemy import Column, String, Boolean, DateTime, Float, Text
from datetime import datetime
import uuid

from database import Base


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)          # 显示名，如 "Claude Sonnet 4.6"
    provider = Column(String(50), nullable=False)        # anthropic | openai | deepseek | qwen
    model_id = Column(String(100), nullable=False)       # 实际调用的模型ID
    api_key = Column(Text)                               # 加密存储（MVP阶段明文，后续加密）
    api_base_url = Column(String(300))                   # 自定义endpoint，部分模型需要
    is_active = Column(Boolean, default=False)           # 当前激活的只能有一个
    price_input = Column(Float, default=0)               # 每百万token价格
    price_output = Column(Float, default=0)
    price_currency = Column(String(3), default="CNY")    # USD 或 CNY
    note = Column(String(300))                           # 备注
    created_at = Column(DateTime, default=datetime.utcnow)
