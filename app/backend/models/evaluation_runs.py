from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text


class Evaluation_runs(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    prompt_version_id = Column(Integer, nullable=True)
    evaluation_case_id = Column(Integer, nullable=False)
    status = Column(String, nullable=True, default="completed")
    score = Column(Float, nullable=True)
    result_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
