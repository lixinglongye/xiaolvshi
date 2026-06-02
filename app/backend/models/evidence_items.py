from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text


class Evidence_items(Base):
    __tablename__ = "evidence_items"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    material_id = Column(Integer, nullable=True)
    evidence_id = Column(String, nullable=True)
    group_no = Column(String, nullable=True)
    sequence_no = Column(Integer, nullable=True)
    evidence_name = Column(String, nullable=False)
    evidence_source = Column(String, nullable=True)
    file_ids_json = Column(Text, nullable=True)
    original_or_copy = Column(String, nullable=True)
    page_range = Column(String, nullable=True)
    proof_purpose = Column(Text, nullable=True)
    related_fact_ids_json = Column(Text, nullable=True)
    related_claim_ids_json = Column(Text, nullable=True)
    weakness = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    manual_status = Column(String, nullable=True, default="AI建议，待律师确认")
    needs_review = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
