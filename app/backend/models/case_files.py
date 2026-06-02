from core.database import Base
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String, Text


class Case_files(Base):
    __tablename__ = "case_files"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    import_job_id = Column(Integer, nullable=True)
    case_id = Column(Integer, nullable=True)
    file_id = Column(String, nullable=False, index=True)
    original_name = Column(String, nullable=False)
    relative_path = Column(String, nullable=True)
    storage_path = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    file_hash = Column(String, nullable=True, index=True)
    size_bytes = Column(BigInteger, nullable=True, default=0)
    page_count = Column(Integer, nullable=True)
    text_extracted = Column(Boolean, nullable=True, default=False)
    ocr_required = Column(Boolean, nullable=True, default=False)
    text_excerpt = Column(Text, nullable=True)
    parsed_text = Column(Text, nullable=True)
    doc_type = Column(String, nullable=True)
    evidence_category = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    parties_detected = Column(Text, nullable=True)
    dates_detected = Column(Text, nullable=True)
    amounts_detected = Column(Text, nullable=True)
    manual_override = Column(Boolean, nullable=True, default=False)
    processing_status = Column(String, nullable=True, default="queued")
    quarantine_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
