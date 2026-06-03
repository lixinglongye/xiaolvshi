from datetime import datetime, timezone

from core.database import Base
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BillingQuotaIdempotencyKey(Base):
    __tablename__ = "billing_quota_idempotency_keys"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_bq_dedup_idempotency_key"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    idempotency_key = Column(String(220), nullable=False, index=True)
    source_event_hash = Column(String(64), nullable=False)
    quota_subject_hash = Column(String(140), nullable=False, index=True)
    quota_window = Column(String(32), nullable=False, index=True)
    usage_metric = Column(String(80), nullable=False, index=True)
    first_seen_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
    seen_count = Column(Integer, nullable=False, default=1)
