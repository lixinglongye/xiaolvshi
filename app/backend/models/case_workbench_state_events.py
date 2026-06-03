from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Index, Integer, JSON, String, UniqueConstraint


class CaseWorkbenchStateEvent(Base):
    __tablename__ = "case_workbench_state_events"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_id",
            name="uq_case_workbench_state_event_user_event",
        ),
        Index("ix_case_workbench_state_events_user_case_section", "user_id", "case_ref_hash", "section"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    case_ref_hash = Column(String, nullable=False, index=True)
    section = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    event_hash = Column(String, nullable=False, index=True)
    state_version = Column(Integer, nullable=False, index=True)
    operation = Column(String, nullable=False)
    event_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
