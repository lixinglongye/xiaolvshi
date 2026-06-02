from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text


class Generated_documents(Base):
    __tablename__ = "generated_documents"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=True)
    doc_type = Column(String, nullable=False)
    user_role = Column(String, nullable=True)
    title = Column(String, nullable=True)
    content = Column(String, nullable=True)
    content_markdown = Column(Text, nullable=True)
    content_json = Column(Text, nullable=True)
    generation_plan_json = Column(Text, nullable=True)
    evidence_citations_json = Column(Text, nullable=True)
    legal_citations_json = Column(Text, nullable=True)
    qa_report_json = Column(Text, nullable=True)
    draft_label = Column(String, nullable=True)
    input_data_json = Column(String, nullable=True)
    citation_map = Column(String, nullable=True)
    status = Column(String, nullable=True)
    generated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
