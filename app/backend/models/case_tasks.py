from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String


class Case_tasks(Base):
    __tablename__ = "case_tasks"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    case_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    status = Column(String, nullable=True)
    related_object_type = Column(String, nullable=True)
    related_object_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
