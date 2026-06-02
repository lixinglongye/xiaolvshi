from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Reviews(Base):
    __tablename__ = "reviews"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    document_id = Column(Integer, nullable=False)
    status = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(String, nullable=True)
    executive_summary = Column(String, nullable=True)
    top_risks_json = Column(String, nullable=True)
    missing_clauses_json = Column(String, nullable=True)
    favorable_clauses_json = Column(String, nullable=True)
    regenerated_clauses_json = Column(String, nullable=True)
    next_steps_json = Column(String, nullable=True)
    disclaimer = Column(String, nullable=True)
    is_paid = Column(Boolean, nullable=True)
    confidence = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)