from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String


class Organization_members(Base):
    __tablename__ = "organization_members"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False)
    org_id = Column(Integer, nullable=False)
    member_email = Column(String, nullable=False)
    member_user_id = Column(String, nullable=True)
    role = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)