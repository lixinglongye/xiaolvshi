from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.case_workbench_section_states import CaseWorkbenchSectionState
from models.case_workbench_state_events import CaseWorkbenchStateEvent
from services.case_workbench_persistence_plan import SECTION_SCHEMAS, SUPPORTED_SECTIONS
from services.case_workbench_risk_refresh_plan import CaseWorkbenchRiskRefreshPlanService
from services.case_workbench_state_repository import CaseWorkbenchStateRepository


RUNTIME_PAYLOAD_ID = "case-workbench-runtime-state-v1"
STATE_SCHEMA_VERSION = "case-workbench-state-v1"
UNSPECIFIED_WORKSPACE_ID = "workspace-unspecified"


class CaseWorkbenchRuntimeBindingService:
    """API-ready facade over repository-backed case workbench state."""

    def __init__(
        self,
        repository: CaseWorkbenchStateRepository | None = None,
        risk_refresh_plan_service: CaseWorkbenchRiskRefreshPlanService | None = None,
    ) -> None:
        self.repository = repository or CaseWorkbenchStateRepository()
        self.risk_refresh_plan_service = risk_refresh_plan_service or CaseWorkbenchRiskRefreshPlanService()

    async def get_state_payload(
        self,
        db: AsyncSession | None = None,
        *,
        user_id: str | None = None,
        case_id: str | None = None,
        workspace_id: str | None = None,
        sections: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        session = self._resolve_db(db)
        owner_id = self._require_text(user_id, "user_id")
        case_ref = self._require_text(case_id, "case_id")
        section_order = self._normalize_sections(sections)

        section_payloads: dict[str, dict[str, Any]] = {}
        loaded_states: list[CaseWorkbenchSectionState] = []
        for section in section_order:
            state = await self.repository.get_state(session, owner_id, case_ref, section)
            if state is not None:
                loaded_states.append(state)
            section_payloads[section] = self._section_to_payload(section, state)

        created_at_values = [state.created_at for state in loaded_states if state.created_at is not None]
        updated_at_values = [state.updated_at for state in loaded_states if state.updated_at is not None]

        payload = {
            "payload_id": RUNTIME_PAYLOAD_ID,
            "case_id": case_ref,
            "workspace_id": self._workspace_id(workspace_id, loaded_states),
            "schema_version": self._schema_version(loaded_states),
            "status": "ready" if loaded_states else "empty",
            "section_order": section_order,
            "section_count": len(section_order),
            "populated_section_count": len(loaded_states),
            "created_at": self._iso(min(created_at_values)) if created_at_values else None,
            "updated_at": self._iso(max(updated_at_values)) if updated_at_values else None,
            "sections": section_payloads,
        }
        recent_events = await self.repository.list_state_events(
            session,
            owner_id,
            case_ref,
            limit=25,
            offset=0,
        )
        payload["risk_refresh_plan"] = self.risk_refresh_plan_service.build_plan(
            payload,
            [self._event_to_payload(event) for event in recent_events],
        )
        return payload

    async def build_state_payload(
        self,
        db: AsyncSession | None = None,
        *,
        user_id: str | None = None,
        case_id: str | None = None,
        workspace_id: str | None = None,
        sections: Iterable[str] | str | None = None,
    ) -> dict[str, Any]:
        return await self.get_state_payload(
            db,
            user_id=user_id,
            case_id=case_id,
            workspace_id=workspace_id,
            sections=sections,
        )

    async def apply_section_state_event(
        self,
        db: AsyncSession | None = None,
        *,
        user_id: str | None = None,
        event: Mapping[str, Any] | None = None,
        return_payload: bool = True,
    ) -> dict[str, Any]:
        session = self._resolve_db(db)
        owner_id = self._require_text(user_id, "user_id")
        if not isinstance(event, Mapping):
            event = {}
        event_id = self._require_text(event.get("event_id"), "event_id")
        case_ref = self._require_text(event.get("case_ref_hash"), "case_ref_hash")
        section = self._require_text(event.get("section"), "section")
        workspace_id = event.get("matter_ref_hash")

        existing_event = await self._get_existing_event(session, owner_id, event_id)
        state_event = await self.repository.append_state_event(session, owner_id, event)
        if existing_event is None:
            state = await self.repository.upsert_section_state(session, owner_id, event)
        else:
            state = await self.repository.get_state(session, owner_id, case_ref, section)

        event_payload = self._event_to_payload(state_event)
        event_payload["created"] = existing_event is None
        event_payload["idempotent_replay"] = existing_event is not None

        result: dict[str, Any] = {
            "status": "idempotent_replay" if existing_event is not None else "applied",
            "case_id": case_ref,
            "workspace_id": self._require_optional_text(workspace_id) or UNSPECIFIED_WORKSPACE_ID,
            "section": section,
            "event": event_payload,
            "section_state": self._section_to_payload(section, state),
        }
        if return_payload:
            result["payload"] = await self.get_state_payload(
                session,
                user_id=owner_id,
                case_id=case_ref,
                workspace_id=self._require_optional_text(workspace_id),
            )
        return result

    async def list_events(
        self,
        db: AsyncSession | None = None,
        *,
        user_id: str | None = None,
        case_id: str | None = None,
        section: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        session = self._resolve_db(db)
        owner_id = self._require_text(user_id, "user_id")
        case_ref = self._require_text(case_id, "case_id")
        section_name = self._require_optional_text(section)
        events = await self.repository.list_state_events(
            session,
            owner_id,
            case_ref,
            section_name,
            limit=limit,
            offset=offset,
        )
        return [self._event_to_payload(event) for event in events]

    async def list_event_audit_trail(
        self,
        db: AsyncSession | None = None,
        *,
        user_id: str | None = None,
        case_id: str | None = None,
        section: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        events = await self.list_events(
            db,
            user_id=user_id,
            case_id=case_id,
            section=section,
            limit=limit,
            offset=offset,
        )
        return {
            "case_id": self._require_text(case_id, "case_id"),
            "section": self._require_optional_text(section),
            "limit": max(1, min(limit, 500)),
            "offset": max(offset, 0),
            "event_count": len(events),
            "events": events,
        }

    async def _get_existing_event(
        self,
        db: AsyncSession,
        user_id: str,
        event_id: str,
    ) -> CaseWorkbenchStateEvent | None:
        result = await db.execute(
            select(CaseWorkbenchStateEvent).where(
                CaseWorkbenchStateEvent.user_id == user_id,
                CaseWorkbenchStateEvent.event_id == event_id,
            )
        )
        return result.scalar_one_or_none()

    def _section_to_payload(
        self,
        section: str,
        state: CaseWorkbenchSectionState | None,
    ) -> dict[str, Any]:
        if state is None:
            return {
                "id": section,
                "status": "empty",
                "schema_version": STATE_SCHEMA_VERSION,
                "state_version": 0,
                "summary": {},
                "state": {},
                "collection_counts": self._empty_collection_counts(section),
                "latest_event_id": None,
                "policy_version": None,
                "validation_status": None,
                "created_at": None,
                "updated_at": None,
            }

        state_delta = self._json_object(state.state_delta_json)
        return {
            "id": section,
            "status": "ready",
            "schema_version": state.schema_version or state_delta.get("schema_version") or STATE_SCHEMA_VERSION,
            "state_version": int(state.state_version or 0),
            "summary": self._json_object(state_delta.get("summary")),
            "state": state_delta,
            "collection_counts": self._collection_counts(section, state_delta),
            "latest_event_id": state.latest_event_id,
            "policy_version": state.policy_version or state_delta.get("policy_version"),
            "validation_status": state.validation_status,
            "created_at": self._iso(state.created_at),
            "updated_at": self._iso(state.updated_at),
        }

    def _event_to_payload(self, event: CaseWorkbenchStateEvent) -> dict[str, Any]:
        event_json = self._json_object(event.event_json)
        return {
            "event_id": event.event_id,
            "case_id": event.case_ref_hash,
            "section": event.section,
            "operation": event.operation,
            "state_version": int(event.state_version or 0),
            "event_hash": event.event_hash,
            "actor_id": event_json.get("actor_ref_hash"),
            "schema_version": event_json.get("schema_version") or STATE_SCHEMA_VERSION,
            "policy_version": event_json.get("policy_version"),
            "validation_status": event_json.get("validation_status"),
            "created_at": self._iso(event.created_at),
            "event_json": event_json,
        }

    def _normalize_sections(self, sections: Iterable[str] | str | None) -> list[str]:
        if sections is None:
            candidates = list(SUPPORTED_SECTIONS)
        elif isinstance(sections, str):
            candidates = [sections]
        else:
            candidates = list(sections)

        normalized: list[str] = []
        for candidate in candidates:
            section = self._require_text(candidate, "section")
            if section not in SUPPORTED_SECTIONS:
                raise ValueError(f"unsupported section: {section}")
            if section not in normalized:
                normalized.append(section)
        return normalized

    def _schema_version(self, states: list[CaseWorkbenchSectionState]) -> str:
        latest_state = self._latest_state(states)
        if latest_state is None:
            return STATE_SCHEMA_VERSION
        return latest_state.schema_version or self._json_object(latest_state.state_delta_json).get("schema_version") or STATE_SCHEMA_VERSION

    def _workspace_id(self, supplied: str | None, states: list[CaseWorkbenchSectionState]) -> str:
        supplied_text = self._require_optional_text(supplied)
        if supplied_text:
            return supplied_text
        latest_state = self._latest_state(states)
        if latest_state is not None and latest_state.matter_ref_hash:
            return latest_state.matter_ref_hash
        return UNSPECIFIED_WORKSPACE_ID

    def _latest_state(self, states: list[CaseWorkbenchSectionState]) -> CaseWorkbenchSectionState | None:
        if not states:
            return None
        return max(states, key=lambda state: (state.updated_at or state.created_at or datetime.min, state.id or 0))

    def _empty_collection_counts(self, section: str) -> dict[str, int]:
        return {collection_name: 0 for collection_name in SECTION_SCHEMAS.get(section, {}).get("collections", {})}

    def _collection_counts(self, section: str, state_delta: dict[str, Any]) -> dict[str, int]:
        counts = self._empty_collection_counts(section)
        for collection_name in counts:
            collection = state_delta.get(collection_name)
            counts[collection_name] = len(collection) if isinstance(collection, list) else 0
        return counts

    def _json_object(self, value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return {str(key): deepcopy(item) for key, item in value.items()}
        return {}

    def _iso(self, value: Any) -> str | None:
        if isinstance(value, datetime):
            return value.isoformat()
        if value is None:
            return None
        return str(value)

    def _resolve_db(self, db: AsyncSession | None) -> AsyncSession:
        session = db or self.repository.db
        if session is None:
            raise ValueError("db is required")
        return session

    def _require_text(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    def _require_optional_text(self, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            return None
        return value.strip()
