from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy
import json

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

from core.database import get_db
from dependencies.auth import get_current_user
from models.case_workbench_section_states import CaseWorkbenchSectionState
from models.case_workbench_state_events import CaseWorkbenchStateEvent
from routers.case_workbench_runtime import router
from schemas.auth import UserResponse


def _event(
    *,
    event_id: str = "cwp-event-runtime-router-parties-001",
    case_ref_hash: str = "case_hash_router_abcdefghijkl",
    state_version: int = 1,
    status: str = "active",
) -> dict:
    return {
        "event_id": event_id,
        "event_type": "case_workbench_state_event",
        "timestamp": f"2026-06-04T08:00:0{state_version}Z",
        "idempotency_key": f"cwp:v1:{case_ref_hash}:parties:{state_version}:src_runtime_router",
        "case_ref_hash": case_ref_hash,
        "matter_ref_hash": "workspace_hash_router_abcdefghijkl",
        "actor_ref_hash": "actor_hash_router_abcdefghijkl",
        "section": "parties",
        "operation": "upsert_snapshot",
        "state_version": state_version,
        "previous_state_version": state_version - 1,
        "schema_version": "case-workbench-state-v1",
        "source_component": "case_workbench_runtime_router",
        "payload_kind": "metadata_snapshot",
        "item_count": 1,
        "changed_item_refs": ["party_hash_router_abcdefghijkl"],
        "changed_field_names": ["party_ref_hash", "party_role", "party_type", "status"],
        "state_delta": {
            "schema_version": "case-workbench-state-v1",
            "section": "parties",
            "state_version": state_version,
            "summary": {"party_count": 1, "review_required_count": 0},
            "updated_by_role": "lawyer",
            "source_component": "case_workbench_runtime_router",
            "policy_version": "case-workbench-persistence-v1",
            "party_states": [
                {
                    "party_ref_hash": "party_hash_router_abcdefghijkl",
                    "party_role": "claimant",
                    "party_type": "individual",
                    "status": status,
                    "representation_status": "represented",
                    "conflict_status": "clear",
                    "identity_verification_status": "verified",
                    "authority_status": "confirmed",
                    "claim_alignment_codes": ["payment_recovery"],
                    "risk_flags": [],
                    "source_refs": ["src_hash_router_001"],
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


@pytest.fixture
def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def _lifespan(_app):
        async with engine.begin() as conn:
            await conn.run_sync(CaseWorkbenchSectionState.__table__.create)
            await conn.run_sync(CaseWorkbenchStateEvent.__table__.create)
        try:
            yield
        finally:
            await engine.dispose()

    app = fastapi.FastAPI(lifespan=_lifespan)
    app.include_router(router)

    async def _override_db():
        async with session_maker() as session:
            yield session

    async def _override_user():
        return UserResponse(
            id="user_hash_router_abcdefghijkl",
            email="router@example.test",
            role="user",
        )

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    with testclient.TestClient(app) as test_client:
        yield test_client


def test_case_workbench_runtime_get_empty_state(client):
    response = client.get(
        "/api/v1/cases/case_hash_empty_router_abcdefghijkl/workbench/state",
        params={"workspace_id": "workspace_hash_empty_router_abcdefghijkl"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "empty"
    assert payload["case_id"] == "case_hash_empty_router_abcdefghijkl"
    assert payload["workspace_id"] == "workspace_hash_empty_router_abcdefghijkl"
    assert payload["populated_section_count"] == 0
    assert payload["sections"]["parties"]["status"] == "empty"
    assert "user_hash_router_abcdefghijkl" not in json.dumps(payload)


def test_case_workbench_runtime_post_applies_metadata_event(client):
    event = _event()

    response = client.post(
        f"/api/v1/cases/{event['case_ref_hash']}/workbench/state-events",
        json=event,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "applied"
    assert payload["case_id"] == event["case_ref_hash"]
    assert payload["workspace_id"] == event["matter_ref_hash"]
    assert payload["event"]["created"] is True
    assert payload["event"]["actor_id"] == "actor_hash_router_abcdefghijkl"
    assert payload["section_state"]["state"]["party_states"][0]["status"] == "active"
    assert payload["payload"]["sections"]["parties"]["collection_counts"] == {"party_states": 1}
    assert "user_hash_router_abcdefghijkl" not in json.dumps(payload)


def test_case_workbench_runtime_get_audit_trail(client):
    case_ref_hash = "case_hash_audit_router_abcdefghijkl"
    event_v2 = _event(
        event_id="cwp-event-runtime-router-audit-002",
        case_ref_hash=case_ref_hash,
        state_version=2,
        status="inactive",
    )
    event_v1 = _event(
        event_id="cwp-event-runtime-router-audit-001",
        case_ref_hash=case_ref_hash,
        state_version=1,
    )

    assert client.post(f"/api/v1/cases/{case_ref_hash}/workbench/state-events", json=event_v2).status_code == 200
    assert client.post(f"/api/v1/cases/{case_ref_hash}/workbench/state-events", json=event_v1).status_code == 200

    response = client.get(
        f"/api/v1/cases/{case_ref_hash}/workbench/state-events",
        params={"section": "parties", "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    trail = response.json()
    assert trail["case_id"] == case_ref_hash
    assert trail["section"] == "parties"
    assert trail["event_count"] == 2
    assert [event["event_id"] for event in trail["events"]] == [
        "cwp-event-runtime-router-audit-001",
        "cwp-event-runtime-router-audit-002",
    ]
    assert [event["state_version"] for event in trail["events"]] == [1, 2]
    assert "user_hash_router_abcdefghijkl" not in json.dumps(trail)


def test_case_workbench_runtime_rejects_path_case_mismatch(client):
    event = deepcopy(_event())
    event["case_ref_hash"] = "case_hash_body_router_abcdefghijkl"

    response = client.post(
        "/api/v1/cases/case_hash_path_router_abcdefghijkl/workbench/state-events",
        json=event,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "case_id does not match event.case_ref_hash"

    audit = client.get(
        "/api/v1/cases/case_hash_body_router_abcdefghijkl/workbench/state-events",
        params={"section": "parties"},
    )
    assert audit.status_code == 200
    assert audit.json()["event_count"] == 0
