from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text


class Subscriptions(Base):
    __tablename__ = "subscriptions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    plan_type = Column(String, nullable=False, default="free")
    status = Column(String, nullable=True, default="active")
    report_quota_monthly = Column(Integer, nullable=True)
    reports_used_month = Column(Integer, nullable=True, default=0)
    team_seats = Column(Integer, nullable=True, default=1)
    features_json = Column(Text, nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
