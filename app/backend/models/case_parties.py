from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String


class Case_parties(Base):
    __tablename__ = "case_parties"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    party_type = Column(String, nullable=True)
    identity_type = Column(String, nullable=True)
    id_number = Column(String, nullable=True)
    address = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    lawyer = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)