from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text


class Claims(Base):
    __tablename__ = "claims"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    claim_no = Column(Integer, nullable=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    calculation_detail = Column(Text, nullable=True)
    legal_basis_ids_json = Column(Text, nullable=True)
    fact_ids_json = Column(Text, nullable=True)
    evidence_ids_json = Column(Text, nullable=True)
    risk_notes = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
