from datetime import datetime, timezone

from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, UniqueConstraint


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BillingQuotaUsageCounter(Base):
    __tablename__ = "billing_quota_usage_counters"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_bq_usage_idempotency_key"),
        UniqueConstraint("source_event_hash", name="uq_bq_usage_source_event_hash"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    idempotency_key = Column(String(220), nullable=False, index=True)
    source_event_hash = Column(String(64), nullable=False, index=True)
    quota_subject_hash = Column(String(140), nullable=False, index=True)
    quota_window = Column(String(32), nullable=False, index=True)
    usage_metric = Column(String(80), nullable=False, index=True)
    units = Column(Integer, nullable=False)
    limit_value = Column(Float, nullable=True)
    used_value = Column(Float, nullable=True)
    remaining_value = Column(Float, nullable=True)
    decision_status = Column(String(40), nullable=False, index=True)
    reason_codes_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
