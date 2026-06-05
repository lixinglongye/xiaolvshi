import json
import re

from services.continuous_session_run_monitor import ContinuousSessionRunMonitorService
from services.legal_review_benchmark import LegalReviewBenchmarkService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _fixture_payload(fixture_id: str, route: str, text: str) -> dict:
    return {
        "phase": "cheap_first",
        "model": "gemini-2.5-flash-lite",
        "http_status": 200,
        "latency_ms": 800,
        "estimated_cost_usd": 0.0002,
        "gateway_response": {
            "model": "gemini-2.5-flash-lite",
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "fixture_id": fixture_id,
                                "route": route,
                                "output_text": text,
                                "release_decision": "pass",
                            },
                            ensure_ascii=False,
                        )
                    }
                }
            ],
        },
    }


def _passing_fixture_review_payload() -> dict:
    fixtures = LegalReviewBenchmarkService().build_fixture_smoke_template()["fixtures"]
    return {
        "responses": {
            fixture["id"]: _fixture_payload(
                fixture["id"],
                fixture["expected_routes"][0],
                " ".join([*fixture["expected_signals"], *fixture["expected_tasks"]]),
            )
            for fixture in fixtures
        }
    }


def _full_window_events():
    return [
        {
            "id": "commit-start",
            "event_type": "commit",
            "timestamp": "2026-06-04T00:00:00Z",
            "commit_hash": "1234567",
            "evidence_paths": ["app/backend/services/continuous_session_run_monitor.py"],
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


def test_run_monitor_defaults_to_not_started_without_claiming_completion():
    monitor = ContinuousSessionRunMonitorService().build_monitor({"current_timestamp": "2026-06-04T00:00:00Z"})

    assert monitor["status"] == "not_started"
    assert monitor["summary"]["completed_medium_large_update_count"] >= 100
    assert monitor["summary"]["update_count_ready"] is True
    assert monitor["summary"]["event_count"] >= 1
    assert monitor["summary"]["submitted_event_count"] == 0
    assert monitor["summary"]["verified_continuous_hours"] == 0
    assert monitor["summary"]["completion_ready"] is False
    assert monitor["summary"]["raw_payload_echoed"] is False
    assert monitor["summary"]["newapi_called"] is False
    assert monitor["run_window"]["start_timestamp"] is None
    assert any(blocker["id"] == "active-events-missing" for blocker in monitor["blockers"])
    assert any(action["id"] == "start-active-run-events" for action in monitor["next_actions"])


def test_run_monitor_tracks_active_window_and_next_checkpoint():
    monitor = ContinuousSessionRunMonitorService().build_monitor(
        {
            "current_timestamp": "2026-06-04T07:00:00Z",
            "checkpoint_interval_hours": 2,
            "max_allowed_gap_hours": 4,
            "events": [
                {
                    "id": "commit-start",
                    "event_type": "commit",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "commit_hash": "1234567",
                },
                {
                    "id": "test-low-resource",
                    "event_type": "test",
                    "timestamp": "2026-06-04T04:00:00Z",
                    "validation_id": "backend-focused",
                    "labels": ["low-resource"],
                },
                {
                    "id": "credential-scan",
                    "event_type": "credential_scan",
                    "timestamp": "2026-06-04T06:00:00Z",
                    "validation_id": "credential-scan",
                },
            ],
        }
    )

    assert monitor["status"] == "running"
    assert monitor["summary"]["elapsed_hours_since_start"] == 7
    assert monitor["summary"]["current_gap_hours"] == 1
    assert monitor["summary"]["next_checkpoint_due_at"] == "2026-06-04T08:00:00Z"
    assert monitor["summary"]["next_checkpoint_due_in_hours"] == 1
    assert monitor["summary"]["required_evidence_ready_count"] >= 3
    assert any(item["event_type"] == "push" and item["status"] == "missing" for item in monitor["required_evidence"])


def test_run_monitor_accepts_archive_safe_fixture_evidence_without_claiming_completion():
    monitor = ContinuousSessionRunMonitorService().build_monitor(
        {
            "current_timestamp": "2026-06-04T01:00:00Z",
            "low_resource_fixture_review": _passing_fixture_review_payload(),
        }
    )
    serialized = json.dumps(monitor, ensure_ascii=False)
    low_resource_required = next(
        item for item in monitor["required_evidence"] if item["event_type"] == "low_resource_legal_fixture"
    )

    assert monitor["status"] == "not_started"
    assert monitor["summary"]["completion_ready"] is False
    assert monitor["summary"]["low_resource_fixture_evidence_status"] == "ready"
    assert monitor["summary"]["low_resource_fixture_evidence_ready"] is True
    assert monitor["summary"]["low_resource_fixture_evidence_release_ready"] is True
    assert monitor["summary"]["low_resource_fixture_evidence_observed_count"] == 4
    assert monitor["summary"]["low_resource_fixture_evidence_archived_count"] == 4
    assert monitor["low_resource_fixture_evidence"]["summary"]["updates_count_mutated"] is False
    assert monitor["low_resource_fixture_evidence"]["summary"]["completion_ready_mutated"] is False
    assert low_resource_required["status"] == "ready"
    assert low_resource_required["fixture_evidence_status"] == "ready"
    assert low_resource_required["observed_fixture_count"] == 4
    assert monitor["source_summaries"]["low_resource_fixture_evidence"]["raw_gateway_response_included"] is False
    assert monitor["privacy_boundary"]["returns_archive_summaries_only"] is True
    assert "run_report_payload" not in serialized
    assert "output_text" not in serialized
    assert "choices" not in serialized


def test_run_monitor_blocks_failed_fixture_evidence_without_echoing_secret():
    secret = "s" + "k-" + ("E" * 24)
    monitor = ContinuousSessionRunMonitorService().build_monitor(
        {
            "current_timestamp": "2026-06-05T00:45:00Z",
            "max_allowed_gap_hours": 5,
            "events": _full_window_events(),
            "low_resource_fixture_review": {
                "fixture_id": "fixture-service-agreement-small",
                "model": "gemini-2.5-flash-lite",
                "gateway_response": {"choices": [{"message": {}}]},
                "http_status": 200,
                "note": f"{secret} raw fixture output should not appear",
            },
        }
    )
    serialized = json.dumps(monitor, ensure_ascii=False)
    low_resource_required = next(
        item for item in monitor["required_evidence"] if item["event_type"] == "low_resource_legal_fixture"
    )

    assert monitor["summary"]["completion_ready"] is False
    assert monitor["summary"]["low_resource_fixture_evidence_status"] == "blocked"
    assert monitor["summary"]["low_resource_fixture_evidence_ready"] is False
    assert low_resource_required["status"] == "blocked"
    assert any(blocker["id"] == "low-resource-fixture-evidence-blocked" for blocker in monitor["blockers"])
    assert any(action["id"] == "review-low-resource-fixture-evidence" for action in monitor["next_actions"])
    assert secret not in serialized
    assert "raw fixture output should not appear" not in serialized
    assert "choices" not in serialized


def test_run_monitor_blocks_when_current_gap_exceeds_policy():
    monitor = ContinuousSessionRunMonitorService().build_monitor(
        {
            "current_timestamp": "2026-06-04T05:30:00Z",
            "max_allowed_gap_hours": 4,
            "events": [
                {
                    "id": "commit-start",
                    "event_type": "commit",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "commit_hash": "1234567",
                }
            ],
        }
    )

    assert monitor["status"] == "blocked"
    assert monitor["summary"]["current_gap_hours"] == 5
    assert any(blocker["id"] == "current-checkpoint-gap-exceeded" for blocker in monitor["blockers"])


def test_run_monitor_ready_only_after_full_reviewable_window():
    monitor = ContinuousSessionRunMonitorService().build_monitor(
        {
            "current_timestamp": "2026-06-05T00:45:00Z",
            "max_allowed_gap_hours": 5,
            "events": _full_window_events(),
        }
    )

    assert monitor["status"] == "ready_for_review"
    assert monitor["summary"]["completion_ready"] is True
    assert monitor["summary"]["verified_continuous_hours"] >= 24
    assert monitor["summary"]["required_evidence_ready_count"] == monitor["summary"]["required_evidence_count"]
    assert monitor["blockers"] == []
    assert monitor["privacy_boundary"]["raw_legal_text_included"] is False


def test_run_monitor_keeps_sensitive_payload_out_of_output():
    monitor = ContinuousSessionRunMonitorService().build_monitor(
        {
            "current_timestamp": "2026-06-04T01:00:00Z",
            "events": [
                {
                    "id": "client@example.com",
                    "event_type": "test",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "validation_id": "s" + "k-" + "a" * 24,
                    "labels": ["password", "low-resource"],
                    "evidence_paths": ["docs/client@example.com.md", "docs/SAFE_PATH.md"],
                    "note": "secret raw client fact",
                }
            ],
        }
    )
    serialized = json.dumps(monitor, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert monitor["summary"]["raw_payload_echoed"] is False
    assert monitor["privacy_boundary"]["credentials_included"] is False


def test_continuous_session_run_monitor_route_returns_template_and_assessment():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/continuous-session-run-monitor")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["summary"]["completion_ready"] is False

    response = client.post(
        "/api/v1/maintenance/continuous-session-run-monitor",
        json={
            "current_timestamp": "2026-06-05T00:45:00Z",
            "max_allowed_gap_hours": 5,
            "events": _full_window_events(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready_for_review"
