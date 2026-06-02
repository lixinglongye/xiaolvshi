from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text


class Risk_items(Base):
    __tablename__ = "risk_items"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    review_id = Column(Integer, nullable=False)
    risk_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=True)
    risk_type = Column(String, nullable=True)
    clause_location = Column(String, nullable=True)
    issue_location = Column(String, nullable=True)
    original_clause = Column(String, nullable=True)
    risk_reason = Column(String, nullable=True)
    user_impact = Column(String, nullable=True)
    suggested_revision = Column(String, nullable=True)
    negotiation_script = Column(String, nullable=True)
    legal_basis = Column(String, nullable=True)
    legal_analysis_json = Column(Text, nullable=True)
    revision_plan_json = Column(Text, nullable=True)
    citations_json = Column(Text, nullable=True)
    confidence = Column(Integer, nullable=True)
    sort_order = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
