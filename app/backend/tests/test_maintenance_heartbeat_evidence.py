import json
import re

from services.maintenance_heartbeat_evidence import MaintenanceHeartbeatEvidenceService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def test_maintenance_heartbeat_evidence_defaults_to_collecting():
    evidence = MaintenanceHeartbeatEvidenceService().build_evidence()

    assert evidence["status"] == "collecting"
    assert evidence["summary"]["target_hours"] == 24
    assert evidence["summary"]["ready_for_goal_claim"] is False
    assert evidence["summary"]["verified_continuous_hours"] == 0
    assert set(evidence["summary"]["missing_event_types"]) == {"commit", "test", "push", "review"}
    assert evidence["validation_commands"]


def test_maintenance_heartbeat_evidence_accepts_reviewable_24h_window():
    events = [
        {
            "id": "commit-start",
            "event_type": "commit",
            "timestamp": "2026-06-04T00:00:00Z",
            "commit_hash": "1234567",
            "evidence_paths": ["app/backend/services/example.py"],
        },
        {
            "id": "test-mid",
            "event_type": "test",
            "timestamp": "2026-06-04T12:00:00Z",
            "validation_id": "backend-tests",
        },
        {
            "id": "review-mid",
            "event_type": "review",
            "timestamp": "2026-06-04T18:00:00Z",
            "validation_id": "credential-scan",
        },
        {
            "id": "push-end",
            "event_type": "push",
            "timestamp": "2026-06-05T01:10:00Z",
            "commit_hash": "abcdef123456",
        },
    ]

    evidence = MaintenanceHeartbeatEvidenceService().build_evidence(events)

    assert evidence["status"] == "ready_for_review"
    assert evidence["summary"]["verified_continuous_hours"] >= 24
    assert evidence["summary"]["missing_event_types"] == []
    assert evidence["summary"]["ready_for_goal_claim"] is True
    assert evidence["gap_analysis"][0]["status"] == "closed"


def test_maintenance_heartbeat_evidence_flags_missing_fields():
    evidence = MaintenanceHeartbeatEvidenceService().build_evidence(
        [
            {
                "id": "bad-commit",
                "event_type": "commit",
                "timestamp": "2026-06-04T00:00:00Z",
            }
        ]
    )
    record = evidence["heartbeat_records"][0]

    assert evidence["status"] == "collecting"
    assert record["status"] == "fail"
    assert record["missing_fields"] == ["commit_hash"]
    assert any(gap["id"] == "invalid-heartbeat-records" for gap in evidence["gap_analysis"])


def test_maintenance_heartbeat_evidence_redacts_sensitive_input():
    evidence = MaintenanceHeartbeatEvidenceService().build_evidence(
        [
            {
                "id": "client@example.com",
                "event_type": "test",
                "timestamp": "2026-06-04T00:00:00Z",
                "validation_id": "s" + "k-" + "a" * 24,
                "evidence_paths": ["docs/secret-client@example.com.md", "docs/SAFE_PATH.md"],
                "note": "password secret",
            }
        ]
    )
    serialized = json.dumps(evidence, ensure_ascii=False)
    record = evidence["heartbeat_records"][0]

    assert not SENSITIVE_PATTERN.search(serialized)
    assert record["id"] == ""
    assert record["validation_id"] == ""
    assert record["evidence_paths"] == ["docs/SAFE_PATH.md"]


def test_maintenance_heartbeat_evidence_route_returns_template():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/maintenance-heartbeat-evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "collecting"
