from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String


class Orders(Base):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    sku = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    currency = Column(String, nullable=True)
    status = Column(String, nullable=True)
    related_review_id = Column(Integer, nullable=True)
    plan_type = Column(String, nullable=True)
    stripe_session_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)