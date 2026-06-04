import json
import re

from services.continuous_session_timeline import ContinuousSessionTimelineService


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
            "validation_id": "legal-fixture-quick-suite",
            "labels": ["low-resource", "quick-suite"],
            "evidence_paths": ["app/backend/tests/test_legal_fixture_quick_suite.py"],
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
            "id": "legal-fixture",
            "event_type": "legal_fixture",
            "timestamp": "2026-06-04T16:00:00Z",
            "validation_id": "legal-document-benchmark-suite",
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


def _validation_events():
    return [
        {
            "id": "validation-test",
            "event_type": "test",
            "timestamp": "2026-06-04T04:00:00Z",
            "validation_id": "backend-focused-pytest",
            "status": "passed",
            "labels": ["low-resource"],
        },
        {
            "id": "validation-scan",
            "event_type": "credential_scan",
            "timestamp": "2026-06-04T08:00:00Z",
            "validation_id": "credential-scan",
            "status": "clean",
        },
        {
            "id": "validation-review",
            "event_type": "release_review",
            "timestamp": "2026-06-04T12:00:00Z",
            "validation_id": "release-readiness",
            "status": "reviewed",
        },
        {
            "id": "validation-fixture",
            "event_type": "legal_fixture",
            "timestamp": "2026-06-04T16:00:00Z",
            "validation_id": "legal-fixture-quick-suite",
            "status": "success",
            "labels": ["quick-suite"],
        },
        {
            "id": "validation-push",
            "event_type": "push",
            "timestamp": "2026-06-04T20:00:00Z",
            "commit_hash": "abcdef123456",
            "status": "pushed",
        },
    ]


def test_continuous_session_timeline_defaults_to_blocked_without_claiming_24h():
    timeline = ContinuousSessionTimelineService().build_timeline()

    assert timeline["status"] in {"collecting", "blocked"}
    assert timeline["summary"]["completed_medium_large_update_count"] >= 100
    assert timeline["summary"]["verified_continuous_hours"] == 0
    assert timeline["summary"]["continuous_hours_remaining"] == 24
    assert timeline["summary"]["completion_ready"] is False
    assert timeline["summary"]["raw_payload_echoed"] is False
    assert any(event["id"] == "ledger-100-plus-checkpoint" for event in timeline["timeline_events"])
    assert "git_history" in timeline["source_summaries"]
    assert "validation_events" in timeline["source_summaries"]
    assert "python -m pytest tests/test_validation_event_evidence.py -q" in timeline["validation_commands"]
    assert "python -m pytest tests/test_git_history_evidence.py -q" in timeline["validation_commands"]
    assert any(blocker["id"] == "timeline-events-missing" for blocker in timeline["blockers"])


def test_continuous_session_timeline_accepts_reviewable_metadata_window():
    timeline = ContinuousSessionTimelineService().build_timeline(
        {
            "max_allowed_gap_hours": 5,
            "events": _reviewable_events(),
        }
    )

    assert timeline["status"] == "ready_for_review"
    assert timeline["summary"]["completion_ready"] is True
    assert timeline["summary"]["verified_continuous_hours"] >= 24
    assert timeline["summary"]["low_resource_event_count"] >= 2
    assert timeline["blockers"] == []
    assert {event["event_type"] for event in timeline["timeline_events"]} >= {
        "commit",
        "test",
        "credential_scan",
        "review",
        "push",
        "ledger_checkpoint",
        "commit_cadence",
    }
    assert any(route.endswith("quick-suite?fixture_limit=2") for route in timeline["low_resource_evidence_routes"])


def test_continuous_session_timeline_keeps_sensitive_input_out_of_output():
    timeline = ContinuousSessionTimelineService().build_timeline(
        {
            "events": [
                {
                    "id": "client@example.com",
                    "event_type": "test",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "validation_id": "s" + "k-" + "a" * 24,
                    "labels": ["password", "low-resource"],
                    "evidence_paths": ["docs/client@example.com.md", "docs/SAFE_PATH.md"],
                    "note": "secret raw client text",
                }
            ],
        }
    )
    serialized = json.dumps(timeline, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert timeline["summary"]["invalid_event_count"] == 1
    assert any(blocker["id"] == "invalid-session-records" for blocker in timeline["blockers"])
    assert timeline["privacy_boundary"]["raw_legal_text_included"] is False


def test_continuous_session_timeline_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/continuous-session-timeline")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["summary"]["completion_ready"] is False

    response = client.post(
        "/api/v1/maintenance/continuous-session-timeline",
        json={"events": _reviewable_events(), "max_allowed_gap_hours": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready_for_review"


def test_continuous_session_timeline_accepts_validation_events_as_non_git_evidence():
    timeline = ContinuousSessionTimelineService().build_timeline(
        {
            "max_allowed_gap_hours": 5,
            "events": [
                {
                    "id": "commit-start",
                    "event_type": "commit",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "commit_hash": "1234567",
                },
                {
                    "id": "commit-end",
                    "event_type": "commit",
                    "timestamp": "2026-06-05T00:30:00Z",
                    "commit_hash": "abcdef9",
                },
            ],
            "validation_events": _validation_events(),
        }
    )

    assert timeline["status"] == "ready_for_review"
    assert timeline["summary"]["completion_ready"] is True
    assert timeline["summary"]["submitted_validation_event_count"] == 5
    assert timeline["summary"]["valid_validation_event_count"] == 5
    assert timeline["source_summaries"]["validation_events"]["ready_for_timeline"] is True
    assert any(event["source"] == "validation_event_evidence" for event in timeline["timeline_events"])
    assert {event["event_type"] for event in timeline["timeline_events"]} >= {
        "commit",
        "test",
        "credential_scan",
        "review",
        "legal_fixture",
        "push",
    }
