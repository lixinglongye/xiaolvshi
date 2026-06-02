from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text


class Review_reports(Base):
    __tablename__ = "review_reports"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    document_id = Column(Integer, nullable=False)
    contract_type = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(String, nullable=True)
    signing_recommendation = Column(String, nullable=True)
    executive_summary = Column(String, nullable=True)
    contract_basic_info = Column(String, nullable=True)
    risk_matrix = Column(String, nullable=True)
    missing_clause_checklist = Column(String, nullable=True)
    favorable_clauses = Column(String, nullable=True)
    legal_source_appendix = Column(String, nullable=True)
    full_report_json = Column(Text, nullable=True)
    pipeline_trace_json = Column(Text, nullable=True)
    disclaimer = Column(String, nullable=True)
    status = Column(String, nullable=True)
    is_paid = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
