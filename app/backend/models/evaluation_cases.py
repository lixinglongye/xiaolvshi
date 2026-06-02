from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text


class Evaluation_cases(Base):
    __tablename__ = "evaluation_cases"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    input_text = Column(Text, nullable=False)
    expected_risks_json = Column(Text, nullable=True)
    expected_sources_json = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    status = Column(String, nullable=True, default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
