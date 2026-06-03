from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Index, Integer, JSON, String, UniqueConstraint


class CaseWorkbenchSectionState(Base):
    __tablename__ = "case_workbench_section_states"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "case_ref_hash",
            "section",
            name="uq_case_workbench_section_state_user_case_section",
        ),
        Index("ix_case_workbench_section_states_user_case", "user_id", "case_ref_hash"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    user_id = Column(String, nullable=False, index=True)
    case_ref_hash = Column(String, nullable=False, index=True)
    matter_ref_hash = Column(String, nullable=True, index=True)
    section = Column(String, nullable=False, index=True)
    state_version = Column(Integer, nullable=False)
    schema_version = Column(String, nullable=True)
    state_delta_json = Column(JSON, nullable=False, default=dict)
    latest_event_id = Column(String, nullable=True)
    policy_version = Column(String, nullable=True)
    validation_status = Column(String, nullable=False, default="pass")
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
