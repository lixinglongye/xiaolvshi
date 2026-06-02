from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LegalKnowledgeArticleResponse(BaseModel):
    id: int
    source_id: str
    source_name: str
    article_number: str
    article_title: Optional[str] = None
    source_type: str
    authority_level: str
    jurisdiction: str
    legal_domain: str
    topics: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    text: str
    summary: Optional[str] = None
    legal_effect_note: Optional[str] = None
    source_url: Optional[str] = None
    official_source_url: Optional[str] = None
    effective_status: str
    verification_status: str
    published_at: Optional[str] = None
    effective_at: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LegalKnowledgeSearchItem(LegalKnowledgeArticleResponse):
    relevance_score: float
    matched_terms: List[str] = Field(default_factory=list)


class LegalKnowledgeSearchResponse(BaseModel):
    query: str
    total: int
    items: List[LegalKnowledgeSearchItem]


class LegalKnowledgeSeedResponse(BaseModel):
    seed_path: str
    dry_run: bool
    inserted: int
    updated: int
    skipped: int
    total_records: int
    errors: List[str] = Field(default_factory=list)


class LegalKnowledgeStatsResponse(BaseModel):
    total: int
    by_domain: dict
    by_source: dict
    by_status: dict
