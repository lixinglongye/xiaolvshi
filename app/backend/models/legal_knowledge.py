from datetime import datetime

from core.database import Base
from sqlalchemy import Column, DateTime, Index, Integer, String, Text


class LegalKnowledgeArticle(Base):
    __tablename__ = "legal_knowledge_articles"
    __table_args__ = (
        Index("ix_legal_knowledge_source_id", "source_id", unique=True),
        Index("ix_legal_knowledge_domain", "legal_domain"),
        Index("ix_legal_knowledge_source_name", "source_name"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    source_id = Column(String, nullable=False, unique=True)
    source_name = Column(String, nullable=False)
    article_number = Column(String, nullable=False)
    article_title = Column(String, nullable=True)
    source_type = Column(String, nullable=False, default="法律")
    authority_level = Column(String, nullable=False, default="裁判依据")
    jurisdiction = Column(String, nullable=False, default="中国大陆")
    legal_domain = Column(String, nullable=False, default="合同审查")
    topics_json = Column(Text, nullable=True)
    keywords_json = Column(Text, nullable=True)
    text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    legal_effect_note = Column(Text, nullable=True)
    source_url = Column(String, nullable=True)
    official_source_url = Column(String, nullable=True)
    effective_status = Column(String, nullable=False, default="现行有效")
    verification_status = Column(String, nullable=False, default="已校验")
    published_at = Column(String, nullable=True)
    effective_at = Column(String, nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    last_seeded_at = Column(DateTime(timezone=True), nullable=True)
    checksum = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
