from core.database import Base
from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text


class Import_jobs(Base):
    __tablename__ = "import_jobs"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    workspace_id = Column(String, nullable=True)
    upload_mode = Column(String, nullable=False, default="auto")
    upload_mode_inferred = Column(String, nullable=True)
    status = Column(String, nullable=False, default="queued")
    original_filename = Column(String, nullable=True)
    stored_path = Column(String, nullable=True)
    total_files = Column(Integer, nullable=True, default=0)
    parsed_files = Column(Integer, nullable=True, default=0)
    total_size_bytes = Column(BigInteger, nullable=True, default=0)
    decompressed_size_bytes = Column(BigInteger, nullable=True, default=0)
    cluster_count = Column(Integer, nullable=True, default=0)
    unclassified_count = Column(Integer, nullable=True, default=0)
    progress = Column(Float, nullable=True, default=0.0)
    clusters_json = Column(Text, nullable=True)
    warnings_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
