from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text


class Legal_sources(Base):
    __tablename__ = "legal_sources"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    source_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    code_ref = Column(String, nullable=True)
    content_snippet = Column(String, nullable=True)
    url = Column(String, nullable=True)
    jurisdiction = Column(String, nullable=True)
    source_name = Column(String, nullable=True)
    article_no = Column(String, nullable=True)
    legal_effect_level = Column(String, nullable=True)
    issuing_authority = Column(String, nullable=True)
    effective_status = Column(String, nullable=True)
    effective_date = Column(String, nullable=True)
    original_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)
    verified = Column(Boolean, nullable=True, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
