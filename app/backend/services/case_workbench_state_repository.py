from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.case_workbench_section_states import CaseWorkbenchSectionState
from models.case_workbench_state_events import CaseWorkbenchStateEvent
from services.case_workbench_persistence_plan import (
    ALLOWED_EVENT_FIELDS,
    COMMON_STATE_FIELDS,
    SECTION_SCHEMAS,
    SUMMARY_FIELDS,
    CaseWorkbenchPersistencePlanService,
)


class CaseWorkbenchStateValidationError(ValueError):
    """Raised when a state event fails the persistence plan privacy contract."""

    def __init__(self, validation_check: dict[str, Any]):
        self.validation_check = deepcopy(validation_check)
        failures = self.validation_check.get("failures") or ["validation_failed"]
        super().__init__("case workbench state event rejected: " + ", ".join(failures))


class CaseWorkbenchStateRepository:
    """Async repository for privacy-safe case workbench state.

    The repository stores only metadata, controlled codes, counts, and opaque
    references accepted by CaseWorkbenchPersistencePlanService.
    """

    def __init__(
        self,
        db: AsyncSession | None = None,
        validator: CaseWorkbenchPersistencePlanService | None = None,
    ):
        self.db = db
        self.validator = validator or CaseWorkbenchPersistencePlanService()

    async def upsert_section_state(
        self,
        db: AsyncSession | None = None,
        user_id: str | None = None,
        event: Mapping[str, Any] | None = None,
    ) -> CaseWorkbenchSectionState:
        session = self._resolve_db(db)
        owner_id = self._require_text(user_id, "user_id")
        event_dict, validation_check = self._validated_event(event)

        case_ref_hash = self._require_text(event_dict.get("case_ref_hash"), "case_ref_hash")
        section = self._require_text(event_dict.get("section"), "section")
        state_delta = self._sanitize_state_delta(event_dict)

        result = await session.execute(
            select(CaseWorkbenchSectionState).where(
                CaseWorkbenchSectionState.user_id == owner_id,
                CaseWorkbenchSectionState.case_ref_hash == case_ref_hash,
                CaseWorkbenchSectionState.section == section,
            )
        )
        state = result.scalar_one_or_none()
        if state is None:
            state = CaseWorkbenchSectionState(
                user_id=owner_id,
                case_ref_hash=case_ref_hash,
                section=section,
            )
            session.add(state)

        state.matter_ref_hash = event_dict.get("matter_ref_hash")
        state.state_version = int(event_dict["state_version"])
        state.schema_version = event_dict.get("schema_version")
        state.state_delta_json = state_delta
        state.latest_event_id = event_dict.get("event_id")
        state.policy_version = event_dict.get("policy_version")
        state.validation_status = validation_check["status"]

        await session.commit()
        await session.refresh(state)
        return state

    async def get_state(
        self,
        db: AsyncSession | None = None,
        user_id: str | None = None,
        case_ref_hash: str | None = None,
        section: str | None = None,
    ) -> CaseWorkbenchSectionState | None:
        session = self._resolve_db(db)
        owner_id = self._require_text(user_id, "user_id")
        case_hash = self._require_text(case_ref_hash, "case_ref_hash")
        section_name = self._require_text(section, "section")

        result = await session.execute(
            select(CaseWorkbenchSectionState).where(
                CaseWorkbenchSectionState.user_id == owner_id,
                CaseWorkbenchSectionState.case_ref_hash == case_hash,
                CaseWorkbenchSectionState.section == section_name,
            )
        )
        return result.scalar_one_or_none()

    async def append_state_event(
        self,
        db: AsyncSession | None = None,
        user_id: str | None = None,
        event: Mapping[str, Any] | None = None,
    ) -> CaseWorkbenchStateEvent:
        session = self._resolve_db(db)
        owner_id = self._require_text(user_id, "user_id")
        event_dict, validation_check = self._validated_event(event)
        event_id = self._require_text(event_dict.get("event_id"), "event_id")
        sanitized_event = self._sanitize_event_json(event_dict, validation_check)
        event_hash = self._event_hash(sanitized_event)

        result = await session.execute(
            select(CaseWorkbenchStateEvent).where(
                CaseWorkbenchStateEvent.user_id == owner_id,
                CaseWorkbenchStateEvent.event_id == event_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            if existing.event_hash != event_hash:
                raise ValueError("case_workbench_state_event_conflict")
            return existing

        state_event = CaseWorkbenchStateEvent(
            user_id=owner_id,
            case_ref_hash=self._require_text(event_dict.get("case_ref_hash"), "case_ref_hash"),
            section=self._require_text(event_dict.get("section"), "section"),
            event_id=event_id,
            event_hash=event_hash,
            state_version=int(event_dict["state_version"]),
            operation=self._require_text(event_dict.get("operation"), "operation"),
            event_json=sanitized_event,
        )
        session.add(state_event)
        await session.commit()
        await session.refresh(state_event)
        return state_event

    async def list_state_events(
        self,
        db: AsyncSession | None = None,
        user_id: str | None = None,
        case_ref_hash: str | None = None,
        section: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CaseWorkbenchStateEvent]:
        session = self._resolve_db(db)
        owner_id = self._require_text(user_id, "user_id")
        case_hash = self._require_text(case_ref_hash, "case_ref_hash")

        query = select(CaseWorkbenchStateEvent).where(
            CaseWorkbenchStateEvent.user_id == owner_id,
            CaseWorkbenchStateEvent.case_ref_hash == case_hash,
        )
        if section is not None:
            query = query.where(CaseWorkbenchStateEvent.section == self._require_text(section, "section"))

        result = await session.execute(
            query.order_by(CaseWorkbenchStateEvent.state_version, CaseWorkbenchStateEvent.id)
            .offset(max(offset, 0))
            .limit(max(1, min(limit, 500)))
        )
        return list(result.scalars().all())

    def _resolve_db(self, db: AsyncSession | None) -> AsyncSession:
        session = db or self.db
        if session is None:
            raise ValueError("db is required")
        return session

    def _validated_event(self, event: Mapping[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
        if not isinstance(event, Mapping):
            check = self.validator.validate_sample_events([event])[0]
            raise CaseWorkbenchStateValidationError(check)

        event_dict = dict(event)
        validation_check = self.validator.validate_sample_events([event_dict])[0]
        if validation_check.get("status") == "fail" or validation_check.get("allowed_to_persist") is False:
            raise CaseWorkbenchStateValidationError(validation_check)
        return event_dict, validation_check

    def _sanitize_event_json(self, event: dict[str, Any], validation_check: dict[str, Any]) -> dict[str, Any]:
        sanitized = {
            field: deepcopy(event[field])
            for field in ALLOWED_EVENT_FIELDS
            if field in event and field != "state_delta"
        }
        if "state_delta" in event:
            sanitized["state_delta"] = self._sanitize_state_delta(event)
        sanitized["validation_status"] = validation_check["status"]
        return sanitized

    def _sanitize_state_delta(self, event: dict[str, Any]) -> dict[str, Any]:
        state_delta = event.get("state_delta")
        section = event.get("section")
        if not isinstance(state_delta, Mapping) or section not in SECTION_SCHEMAS:
            return {}

        sanitized: dict[str, Any] = {}
        for field in COMMON_STATE_FIELDS:
            if field in state_delta:
                sanitized[field] = deepcopy(state_delta[field])

        summary = state_delta.get("summary")
        if isinstance(summary, Mapping):
            sanitized["summary"] = {
                field: deepcopy(summary[field])
                for field in SUMMARY_FIELDS
                if field in summary
            }

        for collection_name, collection_schema in SECTION_SCHEMAS[str(section)]["collections"].items():
            collection_value = state_delta.get(collection_name)
            if not isinstance(collection_value, list):
                continue

            allowed_fields = set(collection_schema["allowed_fields"])
            sanitized[collection_name] = [
                {
                    field: deepcopy(item[field])
                    for field in item
                    if field in allowed_fields
                }
                for item in collection_value
                if isinstance(item, Mapping)
            ]

        return sanitized

    def _event_hash(self, event: dict[str, Any]) -> str:
        canonical = json.dumps(event, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _require_text(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value
