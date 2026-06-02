from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String


class Documents(Base):
    __tablename__ = "documents"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)
    user_role = Column(String, nullable=True)
    file_key = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    status = Column(String, nullable=True)
    language = Column(String, nullable=True)
    extracted_text = Column(String, nullable=True)
    extraction_metadata_json = Column(String, nullable=True)
    extraction_error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
