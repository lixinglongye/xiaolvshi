from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Evidences(Base):
    __tablename__ = "evidences"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    material_id = Column(Integer, nullable=True)
    evidence_no = Column(String, nullable=True)
    title = Column(String, nullable=False)
    evidence_type = Column(String, nullable=True)
    source = Column(String, nullable=True)
    proof_purpose = Column(String, nullable=True)
    related_fact_ids = Column(String, nullable=True)
    authenticity = Column(String, nullable=True)
    relevance = Column(String, nullable=True)
    legality = Column(String, nullable=True)
    risk_note = Column(String, nullable=True)
    need_reinforcement = Column(Boolean, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)