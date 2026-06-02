from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Templates(Base):
    __tablename__ = "templates"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    doc_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=True)
    language = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)