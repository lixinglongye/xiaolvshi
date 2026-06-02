from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text


class Feedback_tickets(Base):
    __tablename__ = "feedback_tickets"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    content = Column(String, nullable=False)
    status = Column(String, nullable=True)
    contact = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    assignee = Column(String, nullable=True)
    resolution_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
