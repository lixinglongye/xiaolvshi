from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text


class Fact_events(Base):
    __tablename__ = "fact_events"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    event_id = Column(String, nullable=True)
    event_date = Column(String, nullable=True)
    date_confidence = Column(Float, nullable=True)
    event_title = Column(String, nullable=False)
    event_detail = Column(Text, nullable=True)
    legal_relevance = Column(Text, nullable=True)
    evidence_refs_json = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    needs_review = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
