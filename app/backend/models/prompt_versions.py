from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text


class Prompt_versions(Base):
    __tablename__ = "prompt_versions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    purpose = Column(String, nullable=False, default="deep_review")
    version = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    user_prompt = Column(Text, nullable=True)
    model = Column(String, nullable=True)
    temperature = Column(Float, nullable=True)
    status = Column(String, nullable=True, default="draft")
    is_active = Column(Boolean, nullable=True, default=False)
    eval_score = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
