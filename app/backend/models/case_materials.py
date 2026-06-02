from core.database import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String


class Case_materials(Base):
    __tablename__ = "case_materials"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    material_no = Column(String, nullable=True)
    title = Column(String, nullable=False)
    material_type = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    parsed_text = Column(String, nullable=True)
    ocr_status = Column(String, nullable=True)
    source = Column(String, nullable=True)
    is_evidence = Column(Boolean, nullable=True)
    proof_purpose = Column(String, nullable=True)
    page_refs = Column(String, nullable=True)
    related_facts = Column(String, nullable=True)
    authenticity_status = Column(String, nullable=True)
    relevance_status = Column(String, nullable=True)
    legality_status = Column(String, nullable=True)
    admissibility_risk = Column(String, nullable=True)
    need_notarization = Column(Boolean, nullable=True)
    source_reliability = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
