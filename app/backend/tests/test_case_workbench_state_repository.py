from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from models.case_workbench_section_states import CaseWorkbenchSectionState
from models.case_workbench_state_events import CaseWorkbenchStateEvent
from services.case_workbench_state_repository import (
    CaseWorkbenchStateRepository,
    CaseWorkbenchStateValidationError,
)


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
    event_id: str = "cwp-event-parties-001",
    case_ref_hash: str = "case_hash_abcdefghijkl",
    state_version: int = 1,
) -> dict:
    return {
        "event_id": event_id,
        "event_type": "case_workbench_state_event",
        "timestamp": "2026-06-04T08:00:00Z",
        "idempotency_key": f"cwp:v1:{case_ref_hash}:parties:{state_version}:src_001",
        "case_ref_hash": case_ref_hash,
        "matter_ref_hash": "matter_hash_abcdefghijkl",
        "actor_ref_hash": "actor_hash_abcdefghijkl",
        "section": "parties",
        "operation": "upsert_snapshot",
        "state_version": state_version,
        "previous_state_version": state_version - 1,
        "schema_version": "case-workbench-state-v1",
        "source_component": "case_workbench_repository",
        "payload_kind": "metadata_snapshot",
        "item_count": 1,
        "changed_item_refs": ["party_hash_abcdefghijkl"],
        "changed_field_names": ["party_ref_hash", "party_role", "party_type", "status"],
        "state_delta": {
            "schema_version": "case-workbench-state-v1",
            "section": "parties",
            "state_version": state_version,
            "summary": {"party_count": 1, "review_required_count": 0},
            "updated_by_role": "lawyer",
            "source_component": "case_workbench_repository",
            "policy_version": "case-workbench-persistence-v1",
            "party_states": [
                {
                    "party_ref_hash": "party_hash_abcdefghijkl",
                    "party_role": "claimant",
                    "party_type": "individual",
                    "status": "active",
                    "representation_status": "represented",
                    "conflict_status": "clear",
                    "identity_verification_status": "verified",
                    "authority_status": "confirmed",
                    "claim_alignment_codes": ["payment_recovery"],
                    "risk_flags": [],
                    "source_refs": ["src_hash_party_001"],
                    "sort_order": 1,
                }
            ],
        },
        "retention_bucket": "active_case_workbench",
        "policy_version": "case-workbench-persistence-v1",
        "review_required": False,
        "validation_status": "pass",
        "created_at": "2026-06-04T08:00:01Z",
    }


@pytest.mark.asyncio
async def test_case_workbench_state_repository_writes_and_reads_compliant_event():
    async with _session() as db:
        repo = CaseWorkbenchStateRepository()
        event = _event()

        state_event = await repo.append_state_event(db, "user-1", event)
        state = await repo.upsert_section_state(db, "user-1", event)

        loaded_state = await repo.get_state(db, "user-1", event["case_ref_hash"], "parties")
        loaded_events = await repo.list_state_events(db, "user-1", event["case_ref_hash"], "parties")

        assert state.id == loaded_state.id
        assert loaded_state.state_version == 1
        assert loaded_state.latest_event_id == event["event_id"]
        assert loaded_state.validation_status == "pass"
        assert loaded_state.state_delta_json["party_states"][0]["party_ref_hash"] == "party_hash_abcdefghijkl"
        assert state_event.id == loaded_events[0].id
        assert loaded_events[0].event_json["validation_status"] == "pass"
        assert loaded_events[0].event_json["state_delta"]["summary"]["party_count"] == 1


@pytest.mark.asyncio
async def test_case_workbench_state_repository_rejects_raw_fields_without_echoing_values():
    async with _session() as db:
        repo = CaseWorkbenchStateRepository()
        event = _event(event_id="cwp-event-raw-001")
        raw_value = "UNSAFE_RAW_CASE_CONTENT_SHOULD_NOT_ECHO"
        email_value = "client@example.com"
        event["client_email"] = email_value
        event["state_delta"]["party_states"][0]["raw_content"] = raw_value

        with pytest.raises(CaseWorkbenchStateValidationError) as event_error:
            await repo.append_state_event(db, "user-1", event)
        with pytest.raises(CaseWorkbenchStateValidationError) as state_error:
            await repo.upsert_section_state(db, "user-1", event)

        rendered = f"{event_error.value} {event_error.value.validation_check} {state_error.value}"
        assert "forbidden_fields_present" in rendered
        assert raw_value not in rendered
        assert email_value not in rendered
        assert await repo.list_state_events(db, "user-1", event["case_ref_hash"], "parties") == []
        assert await repo.get_state(db, "user-1", event["case_ref_hash"], "parties") is None


@pytest.mark.asyncio
async def test_case_workbench_state_repository_isolates_state_and_events_by_user_id():
    async with _session() as db:
        repo = CaseWorkbenchStateRepository()
        case_ref_hash = "case_hash_shared_abcdefghijkl"
        user_a_event = _event(event_id="cwp-event-shared-001", case_ref_hash=case_ref_hash)
        user_b_event = deepcopy(user_a_event)
        user_b_event["state_version"] = 2
        user_b_event["previous_state_version"] = 1
        user_b_event["idempotency_key"] = f"cwp:v1:{case_ref_hash}:parties:2:src_001"
        user_b_event["state_delta"]["state_version"] = 2
        user_b_event["state_delta"]["party_states"][0]["status"] = "inactive"

        await repo.append_state_event(db, "user-a", user_a_event)
        await repo.upsert_section_state(db, "user-a", user_a_event)

        assert await repo.get_state(db, "user-b", case_ref_hash, "parties") is None
        assert await repo.list_state_events(db, "user-b", case_ref_hash, "parties") == []

        await repo.append_state_event(db, "user-b", user_b_event)
        await repo.upsert_section_state(db, "user-b", user_b_event)

        user_a_state = await repo.get_state(db, "user-a", case_ref_hash, "parties")
        user_b_state = await repo.get_state(db, "user-b", case_ref_hash, "parties")
        user_a_events = await repo.list_state_events(db, "user-a", case_ref_hash, "parties")
        user_b_events = await repo.list_state_events(db, "user-b", case_ref_hash, "parties")

        assert user_a_state.state_delta_json["party_states"][0]["status"] == "active"
        assert user_b_state.state_delta_json["party_states"][0]["status"] == "inactive"
        assert len(user_a_events) == 1
        assert len(user_b_events) == 1
        assert user_a_events[0].event_id == user_b_events[0].event_id


@pytest.mark.asyncio
async def test_case_workbench_state_repository_rejects_same_event_id_with_different_payload():
    async with _session() as db:
        repo = CaseWorkbenchStateRepository()
        event = _event(event_id="cwp-event-idempotent-001")

        first = await repo.append_state_event(db, "user-1", event)
        replay = await repo.append_state_event(db, "user-1", deepcopy(event))

        conflicting = deepcopy(event)
        conflicting["state_version"] = 2
        conflicting["previous_state_version"] = 1
        conflicting["state_delta"]["state_version"] = 2
        conflicting["state_delta"]["party_states"][0]["status"] = "inactive"

        with pytest.raises(ValueError) as exc_info:
            await repo.append_state_event(db, "user-1", conflicting)

        events = await repo.list_state_events(db, "user-1", event["case_ref_hash"], "parties")
        assert replay.id == first.id
        assert str(exc_info.value) == "case_workbench_state_event_conflict"
        assert len(events) == 1
        assert events[0].event_hash == first.event_hash
