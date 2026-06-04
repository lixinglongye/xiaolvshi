import json
import re

from services.continuous_session_evidence import ContinuousSessionEvidenceService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _reviewable_events():
    return [
        {
            "id": "commit-start",
            "event_type": "commit",
            "timestamp": "2026-06-04T00:00:00Z",
            "commit_hash": "1234567",
            "evidence_paths": ["app/backend/services/example.py"],
        },
        {
            "id": "test-low-resource",
            "event_type": "test",
            "timestamp": "2026-06-04T04:00:00Z",
            "validation_id": "backend-quick-suite",
            "labels": ["low-resource", "quick-suite"],
        },
        {
            "id": "credential-scan-a",
            "event_type": "credential_scan",
            "timestamp": "2026-06-04T08:00:00Z",
            "validation_id": "credential-scan",
        },
        {
            "id": "review-mid",
            "event_type": "review",
            "timestamp": "2026-06-04T12:00:00Z",
            "validation_id": "release-readiness",
        },
        {
            "id": "benchmark-fixture",
            "event_type": "legal_fixture",
            "timestamp": "2026-06-04T16:00:00Z",
            "validation_id": "legal-fixture-quick-suite",
            "labels": ["low-resource"],
        },
        {
            "id": "push-mid",
            "event_type": "push",
            "timestamp": "2026-06-04T20:00:00Z",
            "commit_hash": "abcdef123456",
        },
        {
            "id": "commit-end",
            "event_type": "commit",
            "timestamp": "2026-06-05T00:30:00Z",
            "commit_hash": "abcdef9",
        },
    ]


def test_continuous_session_evidence_defaults_to_collecting():
    report = ContinuousSessionEvidenceService().build_report()

    assert report["status"] == "collecting"
    assert report["summary"]["target_continuous_hours"] == 24
    assert report["summary"]["completed_medium_large_update_count"] == 0
    assert report["summary"]["ready_for_goal_claim"] is False
    assert report["summary"]["verified_continuous_hours"] == 0
    assert "commit" in report["summary"]["missing_event_types"]
    assert report["summary"]["low_resource_test_evidence"] is False
    assert report["validation_commands"] == ["python -m pytest tests/test_continuous_session_evidence.py -q"]


def test_continuous_session_evidence_accepts_reviewable_24h_window_with_100_updates():
    report = ContinuousSessionEvidenceService().build_report(
        {
            "completed_medium_large_update_count": 100,
            "max_allowed_gap_hours": 5,
            "events": _reviewable_events(),
        }
    )

    assert report["status"] == "ready_for_review"
    assert report["summary"]["verified_continuous_hours"] >= 24
    assert report["summary"]["missing_event_types"] == []
    assert report["summary"]["remaining_medium_large_update_count"] == 0
    assert report["summary"]["low_resource_test_evidence"] is True
    assert report["summary"]["ready_for_goal_claim"] is True
    assert report["best_window"]["record_count"] == len(_reviewable_events())
    assert report["gap_analysis"][0]["id"] == "continuous-session-reviewable"


def test_continuous_session_evidence_rejects_large_middle_gaps():
    events = [
        {
            "id": "commit-start",
            "event_type": "commit",
            "timestamp": "2026-06-04T00:00:00Z",
            "commit_hash": "1234567",
        },
        {
            "id": "push-end",
            "event_type": "push",
            "timestamp": "2026-06-05T02:00:00Z",
            "commit_hash": "abcdef123456",
        },
    ]

    report = ContinuousSessionEvidenceService().build_report(
        {
            "completed_medium_large_update_count": 100,
            "events": events,
        }
    )

    assert report["summary"]["verified_continuous_hours"] == 0
    assert report["summary"]["ready_for_goal_claim"] is False
    assert any(gap["id"] == "continuous-session-window-broken" for gap in report["gap_analysis"])
    assert any(gap["id"] == "required-session-event-types-missing" for gap in report["gap_analysis"])


def test_continuous_session_evidence_redacts_sensitive_input():
    report = ContinuousSessionEvidenceService().build_report(
        {
            "completed_medium_large_update_count": 100,
            "events": [
                {
                    "id": "client@example.com",
                    "event_type": "test",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "validation_id": "s" + "k-" + "a" * 24,
                    "labels": ["password", "low-resource"],
                    "evidence_paths": ["docs/client@example.com.md", "docs/SAFE_PATH.md"],
                    "note": "secret raw matter text",
                }
            ],
        }
    )
    serialized = json.dumps(report, ensure_ascii=False)
    record = report["session_records"][0]

    assert not SENSITIVE_PATTERN.search(serialized)
    assert record["id"] == ""
    assert record["validation_id"] == ""
    assert record["labels"] == ["low-resource"]
    assert record["evidence_paths"] == ["docs/SAFE_PATH.md"]
    assert report["summary"]["invalid_event_count"] == 1


def test_continuous_session_evidence_route_returns_template_and_accepts_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/continuous-session-evidence")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["status"] == "collecting"

    response = client.post(
        "/api/v1/maintenance/continuous-session-evidence",
        json={
            "completed_medium_large_update_count": 100,
            "max_allowed_gap_hours": 5,
            "events": _reviewable_events(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["ready_for_goal_claim"] is True
