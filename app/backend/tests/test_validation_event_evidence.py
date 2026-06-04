import json
import re

from services.validation_event_evidence import ValidationEventEvidenceService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _validation_events():
    return [
        {
            "id": "pytest-focused",
            "event_type": "test",
            "timestamp": "2026-06-04T04:00:00Z",
            "validation_id": "backend-focused-pytest",
            "status": "passed",
            "labels": ["low-resource"],
            "evidence_paths": ["app/backend/tests/test_validation_event_evidence.py"],
        },
        {
            "id": "scan-clean",
            "event_type": "credential_scan",
            "timestamp": "2026-06-04T08:00:00Z",
            "check_id": "credential-scan",
            "status": "clean",
            "evidence_paths": ["docs/VALIDATION_EVENT_EVIDENCE.md"],
        },
        {
            "id": "remote-push",
            "event_type": "push",
            "timestamp": "2026-06-04T12:00:00Z",
            "commit_hash": "abcdef123456",
            "status": "pushed",
        },
        {
            "id": "release-review",
            "event_type": "release_review",
            "timestamp": "2026-06-04T16:00:00Z",
            "validation_id": "release-readiness-review",
            "status": "reviewed",
        },
        {
            "id": "fixture-quick",
            "event_type": "legal_fixture",
            "timestamp": "2026-06-04T20:00:00Z",
            "run_id": "legal-fixture-quick-suite",
            "status": "success",
            "labels": ["quick-suite"],
            "evidence_paths": ["app/backend/tests/test_legal_fixture_quick_suite.py"],
        },
    ]


def test_validation_event_evidence_defaults_to_collecting_without_claiming_goal():
    report = ValidationEventEvidenceService().build_evidence()

    assert report["status"] == "collecting"
    assert report["summary"]["event_count"] == 0
    assert report["summary"]["ready_for_timeline"] is False
    assert report["summary"]["ready_for_goal_claim"] is False
    assert set(report["summary"]["missing_event_types"]) == {
        "test",
        "credential_scan",
        "push",
        "review",
        "legal_fixture",
    }
    assert report["missing_event_types"] == report["summary"]["missing_event_types"]
    assert report["privacy_boundary"]["raw_logs_included"] is False


def test_validation_event_evidence_normalizes_passed_metadata_for_timeline():
    report = ValidationEventEvidenceService().build_evidence({"events": _validation_events()})

    assert report["status"] == "ready_for_timeline"
    assert report["summary"]["event_count"] == 5
    assert report["summary"]["invalid_event_count"] == 0
    assert report["summary"]["missing_event_types"] == []
    assert report["summary"]["low_resource_legal_fixture_evidence"] is True
    assert report["summary"]["ready_for_goal_claim"] is False
    assert {event["event_type"] for event in report["normalized_session_events"]} == {
        "test",
        "credential_scan",
        "push",
        "review",
        "legal_fixture",
    }
    assert any(event["event_type"] == "review" for event in report["normalized_session_events"])
    assert all(event["id"].startswith("validation-") for event in report["normalized_session_events"])


def test_validation_event_evidence_rejects_raw_or_sensitive_payload_fields():
    report = ValidationEventEvidenceService().build_evidence(
        {
            "events": [
                {
                    "id": "client@example.com",
                    "event_type": "test",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "validation_id": "s" + "k-" + "a" * 24,
                    "status": "passed",
                    "stdout": "secret raw client text",
                    "labels": ["password", "low-resource"],
                    "evidence_paths": ["docs/client@example.com.md", "docs/SAFE_PATH.md"],
                }
            ]
        }
    )
    serialized = json.dumps(report, ensure_ascii=False)

    assert report["summary"]["invalid_event_count"] == 1
    assert report["event_reviews"][0]["status"] == "fail"
    assert "metadata_only" in report["event_reviews"][0]["missing_fields"]
    assert "stdout" in report["event_reviews"][0]["rejected_fields"]
    assert not SENSITIVE_PATTERN.search(serialized)
    assert report["privacy_boundary"]["raw_stdout_included"] is False


def test_validation_event_evidence_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/validation-event-evidence")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["summary"]["ready_for_timeline"] is False

    response = client.post(
        "/api/v1/maintenance/validation-event-evidence",
        json={"events": _validation_events()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready_for_timeline"
