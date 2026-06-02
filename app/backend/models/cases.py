from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String


class Cases(Base):
    __tablename__ = "cases"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    org_id = Column(Integer, nullable=True)
    client_name = Column(String, nullable=True)
    title = Column(String, nullable=False)
    case_type = Column(String, nullable=True)
    stage = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    court_or_arbitration = Column(String, nullable=True)
    role = Column(String, nullable=True)
    opposing_party = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    summary = Column(String, nullable=True)
    dispute_focus = Column(String, nullable=True)
    claims = Column(String, nullable=True)
    legal_basis = Column(String, nullable=True)
    missing_materials = Column(String, nullable=True)
    next_steps = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    team_members = Column(String, nullable=True)
    key_deadline = Column(String, nullable=True)
    material_count = Column(Integer, nullable=True)
    evidence_completeness = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
