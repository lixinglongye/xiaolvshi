import json
import re

from services.continuous_session_review_packet import ContinuousSessionReviewPacketService
from services.legal_review_benchmark import LegalReviewBenchmarkService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _git_events():
    return [
        {"commit_hash": "a111111", "timestamp": "2026-06-04T00:00:00Z", "title": "Start session"},
        {"commit_hash": "b222222", "timestamp": "2026-06-04T05:00:00Z", "title": "Add fixtures"},
        {"commit_hash": "c333333", "timestamp": "2026-06-04T10:00:00Z", "title": "Review gates"},
        {"commit_hash": "d444444", "timestamp": "2026-06-04T15:00:00Z", "title": "Add UI"},
        {"commit_hash": "e555555", "timestamp": "2026-06-04T20:00:00Z", "title": "Push evidence"},
        {"commit_hash": "f666666", "timestamp": "2026-06-05T01:00:00Z", "title": "Complete review packet"},
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


def _reviewable_payload():
    return {
        "max_allowed_gap_hours": 5,
        "events": [
            {"id": "commit-start", "event_type": "commit", "timestamp": "2026-06-04T00:00:00Z", "commit_hash": "1234567"},
            {"id": "commit-end", "event_type": "commit", "timestamp": "2026-06-05T00:30:00Z", "commit_hash": "abcdef9"},
        ],
        "validation_events": _validation_events(),
        "git_history": {"events": _git_events(), "max_allowed_gap_hours": 6},
    }


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


def test_review_packet_defaults_to_collecting_without_claiming_completion():
    packet = ContinuousSessionReviewPacketService().build_packet()

    assert packet["status"] in {"collecting", "blocked"}
    assert packet["summary"]["update_count_ready"] is True
    assert packet["summary"]["timeline_completion_ready"] is False
    assert packet["summary"]["packet_ready_for_support_claim"] is False
    assert packet["summary"]["raw_payload_echoed"] is False
    assert len(packet["summary"]["packet_hash"]) == 16
    assert {section["id"] for section in packet["packet_sections"]} >= {
        "update-ledger",
        "timeline-window",
        "git-cadence",
        "validation-events",
        "privacy-boundary",
    }
    assert packet["privacy_boundary"]["raw_legal_text_included"] is False


def test_review_packet_accepts_complete_metadata_without_raw_payload():
    packet = ContinuousSessionReviewPacketService().build_packet(_reviewable_payload())
    repeated = ContinuousSessionReviewPacketService().build_packet(_reviewable_payload())

    assert packet["status"] == "ready_for_review"
    assert packet["summary"]["packet_ready_for_support_claim"] is True
    assert packet["summary"]["timeline_completion_ready"] is True
    assert packet["summary"]["git_cadence_ready"] is True
    assert packet["summary"]["validation_events_ready"] is True
    assert packet["summary"]["hard_blocker_count"] == 0
    assert packet["summary"]["packet_hash"] == repeated["summary"]["packet_hash"]
    assert all(section["status"] == "pass" for section in packet["packet_sections"])
    assert packet["blockers"] == []
    assert any("timestamped events" in question for question in packet["reviewer_questions"])


def test_review_packet_summarizes_low_resource_fixture_review_without_raw_output():
    payload = _reviewable_payload()
    payload["low_resource_fixture_review"] = _passing_fixture_review_payload()
    packet = ContinuousSessionReviewPacketService().build_packet(payload)
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["status"] == "ready_for_review"
    assert packet["summary"]["low_resource_fixture_review_status"] == "ready"
    assert packet["summary"]["low_resource_fixture_review_ready"] is True
    assert packet["summary"]["low_resource_fixture_review_release_ready"] is True
    assert packet["summary"]["low_resource_fixture_review_observed_count"] == 4
    assert packet["summary"]["low_resource_fixture_review_raw_payload_echoed"] is False
    assert packet["source_summaries"]["low_resource_fixture_review"]["raw_gateway_response_included"] is False
    assert packet["source_summaries"]["low_resource_fixture_review"]["check_status_counts"]["pass"] >= 5
    assert packet["privacy_boundary"]["raw_gateway_response_included"] is False
    assert "run_report_payload" not in serialized
    assert "output_text" not in serialized
    assert "choices" not in serialized


def test_review_packet_blocks_failed_fixture_review_without_echoing_secret():
    secret = "s" + "k-" + ("C" * 24)
    packet = ContinuousSessionReviewPacketService().build_packet(
        {
            **_reviewable_payload(),
            "low_resource_fixture_review": {
                "fixture_id": "fixture-service-agreement-small",
                "model": "gemini-2.5-flash-lite",
                "gateway_response": {"choices": [{"message": {}}]},
                "http_status": 200,
                "note": f"{secret} raw fixture output should not appear",
            },
        }
    )
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["status"] == "collecting"
    assert packet["summary"]["low_resource_fixture_review_status"] == "fail"
    assert packet["summary"]["low_resource_fixture_review_ready"] is False
    assert packet["summary"]["low_resource_fixture_review_blocked"] is True
    assert packet["summary"]["packet_ready_for_support_claim"] is False
    assert any(blocker["id"] == "low-resource-legal-fixture-not-ready" for blocker in packet["blockers"])
    assert secret not in serialized
    assert "raw fixture output should not appear" not in serialized


def test_review_packet_keeps_sensitive_payload_out_of_output():
    packet = ContinuousSessionReviewPacketService().build_packet(
        {
            "events": [
                {
                    "id": "client@example.com",
                    "event_type": "test",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "validation_id": "s" + "k-" + "a" * 24,
                    "note": "secret raw client text",
                    "labels": ["password"],
                }
            ],
            "validation_events": [
                {
                    "id": "client@example.com",
                    "event_type": "test",
                    "timestamp": "2026-06-04T00:00:00Z",
                    "validation_id": "s" + "k-" + "b" * 24,
                    "status": "passed",
                    "stdout": "secret raw client text",
                }
            ],
        }
    )
    serialized = json.dumps(packet, ensure_ascii=False)

    assert not SENSITIVE_PATTERN.search(serialized)
    assert packet["summary"]["packet_ready_for_support_claim"] is False
    assert packet["privacy_boundary"]["raw_logs_included"] is False
    assert any(blocker["id"] == "invalid-validation-events" for blocker in packet["blockers"])


def test_review_packet_route_returns_template_and_packet():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get("/api/v1/maintenance/continuous-session-review-packet")
    assert template_response.status_code == 200
    assert template_response.json()["data"]["summary"]["packet_ready_for_support_claim"] is False

    response = client.post(
        "/api/v1/maintenance/continuous-session-review-packet",
        json={**_reviewable_payload(), "low_resource_fixture_review": _passing_fixture_review_payload()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready_for_review"
    assert payload["data"]["summary"]["low_resource_fixture_review_observed_count"] == 4
