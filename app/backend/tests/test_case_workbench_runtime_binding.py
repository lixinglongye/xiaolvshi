from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy
import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from models.case_workbench_section_states import CaseWorkbenchSectionState
from models.case_workbench_state_events import CaseWorkbenchStateEvent
from services.case_workbench_runtime_binding import CaseWorkbenchRuntimeBindingService


@asynccontextmanager
async def _session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(CaseWorkbenchSectionState.__table__.create)
        await conn.run_sync(CaseWorkbenchStateEvent.__table__.create)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            yield session
    finally:
        await engine.dispose()


def _event(
    *,
    event_id: str = "cwp-event-runtime-parties-001",
    case_ref_hash: str = "case_hash_runtime_abcdefghijkl",
    state_version: int = 1,
    status: str = "active",
) -> dict:
    return {
        "event_id": event_id,
        "event_type": "case_workbench_state_event",
        "timestamp": f"2026-06-04T08:00:0{state_version}Z",
        "idempotency_key": f"cwp:v1:{case_ref_hash}:parties:{state_version}:src_runtime",
        "case_ref_hash": case_ref_hash,
        "matter_ref_hash": "workspace_hash_runtime_abcdefghijkl",
        "actor_ref_hash": "actor_hash_runtime_abcdefghijkl",
        "section": "parties",
        "operation": "upsert_snapshot",
        "state_version": state_version,
        "previous_state_version": state_version - 1,
        "schema_version": "case-workbench-state-v1",
        "source_component": "case_workbench_runtime_binding",
        "payload_kind": "metadata_snapshot",
        "item_count": 1,
        "changed_item_refs": ["party_hash_runtime_abcdefghijkl"],
        "changed_field_names": ["party_ref_hash", "party_role", "party_type", "status"],
        "state_delta": {
            "schema_version": "case-workbench-state-v1",
            "section": "parties",
            "state_version": state_version,
            "summary": {"party_count": 1, "review_required_count": 0},
            "updated_by_role": "lawyer",
            "source_component": "case_workbench_runtime_binding",
            "policy_version": "case-workbench-persistence-v1",
            "party_states": [
                {
                    "party_ref_hash": "party_hash_runtime_abcdefghijkl",
                    "party_role": "claimant",
                    "party_type": "individual",
                    "status": status,
                    "representation_status": "represented",
                    "conflict_status": "clear",
                    "identity_verification_status": "verified",
                    "authority_status": "confirmed",
                    "claim_alignment_codes": ["payment_recovery"],
                    "risk_flags": [],
                    "source_refs": ["src_hash_runtime_001"],
                    "sort_order": 1,
                }
            ],
        },
        "retention_bucket": "active_case_workbench",
        "policy_version": "case-workbench-persistence-v1",
        "review_required": False,
        "validation_status": "pass",
        "created_at": f"2026-06-04T08:00:1{state_version}Z",
    }


@pytest.mark.asyncio
async def test_runtime_binding_returns_empty_state_payload_for_case_workspace():
    async with _session() as db:
        service = CaseWorkbenchRuntimeBindingService()

        payload = await service.get_state_payload(
            db,
            user_id="user_hash_runtime_abcdefghijkl",
            case_id="case_hash_empty_abcdefghijkl",
            workspace_id="workspace_hash_empty_abcdefghijkl",
        )

        assert payload["payload_id"] == "case-workbench-runtime-state-v1"
        assert payload["status"] == "empty"
        assert payload["case_id"] == "case_hash_empty_abcdefghijkl"
        assert payload["workspace_id"] == "workspace_hash_empty_abcdefghijkl"
        assert payload["schema_version"] == "case-workbench-state-v1"
        assert payload["created_at"] is None
        assert payload["updated_at"] is None
        assert payload["populated_section_count"] == 0
        assert set(payload["sections"]) == {"parties", "facts", "tasks", "deadlines", "evidence_graph"}
        assert payload["sections"]["parties"]["status"] == "empty"
        assert payload["sections"]["parties"]["collection_counts"] == {"party_states": 0}
        assert "user_hash_runtime_abcdefghijkl" not in json.dumps(payload)


@pytest.mark.asyncio
async def test_runtime_binding_applies_event_and_returns_aggregated_payload():
    async with _session() as db:
        service = CaseWorkbenchRuntimeBindingService()
        event = _event()

        result = await service.apply_section_state_event(
            db,
            user_id="user_hash_runtime_abcdefghijkl",
            event=event,
        )

        payload = result["payload"]
        parties = payload["sections"]["parties"]
        assert result["status"] == "applied"
        assert result["event"]["created"] is True
        assert result["event"]["idempotent_replay"] is False
        assert result["event"]["actor_id"] == "actor_hash_runtime_abcdefghijkl"
        assert payload["status"] == "ready"
        assert payload["case_id"] == event["case_ref_hash"]
        assert payload["workspace_id"] == event["matter_ref_hash"]
        assert payload["created_at"] is not None
        assert payload["updated_at"] is not None
        assert payload["populated_section_count"] == 1
        assert parties["status"] == "ready"
        assert parties["state_version"] == 1
        assert parties["summary"] == {"party_count": 1, "review_required_count": 0}
        assert parties["collection_counts"] == {"party_states": 1}
        assert parties["state"]["party_states"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_runtime_binding_replays_same_event_idempotently():
    async with _session() as db:
        service = CaseWorkbenchRuntimeBindingService()
        event = _event(event_id="cwp-event-runtime-idempotent-001")

        first = await service.apply_section_state_event(db, user_id="user_hash_runtime_abcdefghijkl", event=event)
        replay = await service.apply_section_state_event(db, user_id="user_hash_runtime_abcdefghijkl", event=deepcopy(event))
        events = await service.list_events(
            db,
            user_id="user_hash_runtime_abcdefghijkl",
            case_id=event["case_ref_hash"],
        )

        assert first["event"]["event_hash"] == replay["event"]["event_hash"]
        assert replay["status"] == "idempotent_replay"
        assert replay["event"]["created"] is False
        assert replay["event"]["idempotent_replay"] is True
        assert len(events) == 1
        assert replay["payload"]["sections"]["parties"]["state_version"] == 1


@pytest.mark.asyncio
async def test_runtime_binding_replay_does_not_downgrade_newer_section_state():
    async with _session() as db:
        service = CaseWorkbenchRuntimeBindingService()
        case_ref_hash = "case_hash_replay_newer_abcdefghijkl"
        event_v1 = _event(
            event_id="cwp-event-runtime-replay-newer-001",
            case_ref_hash=case_ref_hash,
            state_version=1,
        )
        event_v2 = _event(
            event_id="cwp-event-runtime-replay-newer-002",
            case_ref_hash=case_ref_hash,
            state_version=2,
            status="inactive",
        )

        await service.apply_section_state_event(db, user_id="user_hash_runtime_abcdefghijkl", event=event_v1)
        await service.apply_section_state_event(db, user_id="user_hash_runtime_abcdefghijkl", event=event_v2)
        replay = await service.apply_section_state_event(
            db,
            user_id="user_hash_runtime_abcdefghijkl",
            event=deepcopy(event_v1),
        )

        parties = replay["payload"]["sections"]["parties"]
        assert replay["status"] == "idempotent_replay"
        assert parties["state_version"] == 2
        assert parties["state"]["party_states"][0]["status"] == "inactive"


@pytest.mark.asyncio
async def test_runtime_binding_rejects_same_event_id_with_different_content():
    async with _session() as db:
        service = CaseWorkbenchRuntimeBindingService()
        event = _event(event_id="cwp-event-runtime-conflict-001")
        await service.apply_section_state_event(db, user_id="user_hash_runtime_abcdefghijkl", event=event)

        conflicting = deepcopy(event)
        conflicting["state_version"] = 2
        conflicting["previous_state_version"] = 1
        conflicting["state_delta"]["state_version"] = 2
        conflicting["state_delta"]["party_states"][0]["status"] = "inactive"

        with pytest.raises(ValueError, match="case_workbench_state_event_conflict"):
            await service.apply_section_state_event(
                db,
                user_id="user_hash_runtime_abcdefghijkl",
                event=conflicting,
            )

        events = await service.list_events(
            db,
            user_id="user_hash_runtime_abcdefghijkl",
            case_id=event["case_ref_hash"],
        )
        payload = await service.get_state_payload(
            db,
            user_id="user_hash_runtime_abcdefghijkl",
            case_id=event["case_ref_hash"],
        )

        assert len(events) == 1
        assert payload["sections"]["parties"]["state"]["party_states"][0]["status"] == "active"


@pytest.mark.asyncio
async def test_runtime_binding_lists_audit_trail_sorted_and_serializable():
    async with _session() as db:
        service = CaseWorkbenchRuntimeBindingService()
        case_ref_hash = "case_hash_audit_abcdefghijkl"
        event_v2 = _event(
            event_id="cwp-event-runtime-audit-002",
            case_ref_hash=case_ref_hash,
            state_version=2,
            status="inactive",
        )
        event_v1 = _event(
            event_id="cwp-event-runtime-audit-001",
            case_ref_hash=case_ref_hash,
            state_version=1,
        )

        await service.apply_section_state_event(db, user_id="user_hash_runtime_abcdefghijkl", event=event_v2)
        await service.apply_section_state_event(db, user_id="user_hash_runtime_abcdefghijkl", event=event_v1)
        trail = await service.list_event_audit_trail(
            db,
            user_id="user_hash_runtime_abcdefghijkl",
            case_id=case_ref_hash,
            section="parties",
        )

        assert trail["event_count"] == 2
        assert [event["event_id"] for event in trail["events"]] == [
            "cwp-event-runtime-audit-001",
            "cwp-event-runtime-audit-002",
        ]
        assert [event["state_version"] for event in trail["events"]] == [1, 2]
        assert all(isinstance(event["created_at"], str) for event in trail["events"])
        assert trail["events"][0]["event_json"]["state_delta"]["party_states"][0]["status"] == "active"
        json.dumps(trail, sort_keys=True)
