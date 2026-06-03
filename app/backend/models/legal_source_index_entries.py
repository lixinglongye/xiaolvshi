from __future__ import annotations

from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Index, Integer, String, UniqueConstraint


class LegalSourceIndexEntryRecord(Base):
    __tablename__ = "legal_source_index_entries"
    __table_args__ = (
        UniqueConstraint("source_id", name="uq_legal_source_index_entries_source_id"),
        UniqueConstraint("index_entry_id", name="uq_legal_source_index_entries_index_entry_id"),
        Index("ix_legal_source_index_entries_query", "jurisdiction", "source_type", "freshness_status"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    source_id = Column(String, nullable=False, index=True)
    index_entry_id = Column(String, nullable=False, index=True)
    index_version = Column(String, nullable=False, index=True)
    source_type = Column(String, nullable=False, index=True)
    jurisdiction = Column(String, nullable=False, index=True)
    effective_date = Column(String, nullable=False, index=True)
    citation = Column(String, nullable=False, index=True)
    citation_key = Column(String, nullable=True, index=True)
    dedupe_key = Column(String, nullable=False, index=True)
    freshness_status = Column(String, nullable=False, index=True)
    freshness_expires_at = Column(String, nullable=False)
    metadata_hash = Column(String, nullable=False)
    use_case = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    source_title = Column(String, nullable=True)
    last_verified_at = Column(String, nullable=False, index=True)
    authority_level = Column(String, nullable=True, index=True)
    issuer = Column(String, nullable=True, index=True)
    publication_date = Column(String, nullable=True)
    amendment_date = Column(String, nullable=True)
    official_url = Column(String, nullable=True)
    retrieval_locator = Column(String, nullable=True)
    content_hash = Column(String, nullable=True)
    ingestion_batch_id = Column(String, nullable=True)
    indexed_at = Column(String, nullable=True)
    retention_bucket = Column(String, nullable=True, index=True)
    effective_title_key = Column(String, nullable=True)
    content_hash_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
