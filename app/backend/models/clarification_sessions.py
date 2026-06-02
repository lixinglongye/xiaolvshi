from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text


class Clarification_sessions(Base):
    __tablename__ = "clarification_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=True)
    task_type = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    status = Column(String, nullable=False, default="active")
    understanding = Column(Text, nullable=True)
    slots_json = Column(Text, nullable=True)
    missing_required_json = Column(Text, nullable=True)
    missing_optional_json = Column(Text, nullable=True)
    conflicts_json = Column(Text, nullable=True)
    questions_json = Column(Text, nullable=True)
    user_answers_json = Column(Text, nullable=True)
    generation_plan_json = Column(Text, nullable=True)
    completeness_score = Column(Float, nullable=True, default=0.0)
    can_generate_draft_with_assumptions = Column(Boolean, nullable=True, default=True)
    assumptions_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
