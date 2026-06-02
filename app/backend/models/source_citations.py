from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String


class Source_citations(Base):
    __tablename__ = "source_citations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    risk_item_id = Column(Integer, nullable=False)
    legal_source_id = Column(Integer, nullable=False)
    snippet = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)