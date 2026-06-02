from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Case_facts(Base):
    __tablename__ = "case_facts"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    fact_no = Column(String, nullable=True)
    event_date = Column(String, nullable=True)
    fact_text = Column(String, nullable=False)
    persons = Column(String, nullable=True)
    amount = Column(String, nullable=True)
    source_refs = Column(String, nullable=True)
    confidence = Column(String, nullable=True)
    verified_by_user = Column(Boolean, nullable=True)
    contradiction_note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)