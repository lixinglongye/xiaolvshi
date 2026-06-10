import json
import re

from services.legal_document_benchmark_route_plan_execution_review_packet import (
    REVIEW_PACKET_ID,
    LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|access[_-]?token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def _planned_observation(case_id: str, *, phase: str = "primary") -> dict:
    service = LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService()
    route_plan = service.readiness_service.route_plan_service.build_plan()
    row = {item["case_id"]: item for item in route_plan["case_route_rows"]}[case_id]
    expected_model = row["precheck_route"]["model"] if phase == "precheck" else row["primary_route"]["resolved_model"]
    return {
        "case_id": case_id,
        "phase": phase,
        "observed_model": expected_model,
        "observed_status": "success",
        "observed_input_tokens": 1200,
        "observed_output_tokens": 256,
        "observed_cost_usd": 0.0002,
        "latency_ms": 1200,
    }


def test_route_plan_execution_review_packet_builds_review_template():
    packet = LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService().build_packet()

    assert packet["id"] == REVIEW_PACKET_ID
    assert packet["status"] == "review_required"
    assert packet["summary"]["readiness_status"] == "ready"
    assert packet["summary"]["archive_status"] == "not_run"
    assert packet["summary"]["handoff_status"] == "review_required"
    assert packet["summary"]["observation_count"] == 0
    assert packet["summary"]["ready_for_release_packet"] is False
    assert packet["summary"]["release_action"] == "collect_manual_observations_before_review_packet"
    assert packet["summary"]["model_called"] is False
    assert packet["summary"]["network_called"] is False
    assert packet["summary"]["benchmark_executed"] is False
    assert packet["review_packet_policy"]["records_maintainer_approval"] is False
    assert packet["review_packet_policy"]["writes_release_record"] is False
    assert "result-archive-review-packet-linked" in packet["warning_check_ids"]
    assert not SENSITIVE_PATTERN.search(json.dumps(packet, ensure_ascii=False))


def test_route_plan_execution_review_packet_accepts_ready_handoff():
    packet = LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService().build_packet(
        {
            "observations": [
                _planned_observation("ldoc-contract-review-mini"),
                _planned_observation("ldoc-civil-complaint-mini", phase="precheck"),
            ]
        }
    )
    review_items = {item["id"]: item for item in packet["review_items"]}
    claim_rows = {row["id"]: row for row in packet["claim_review_rows"]}

    assert packet["status"] == "ready"
    assert packet["summary"]["archive_status"] == "ready"
    assert packet["summary"]["handoff_status"] == "ready"
    assert packet["summary"]["ready_for_release_packet"] is True
    assert packet["summary"]["release_action"] == "attach_review_packet_to_release_evidence"
    assert packet["summary"]["attachable_row_count"] == 2
    assert review_items["execution-result-handoff"]["release_action"] == "attach_to_release_evidence"
    assert claim_rows["sanitized-route-plan-result-evidence"]["allowed"] is True
    assert claim_rows["public-benchmark-score"]["allowed"] is False


def test_route_plan_execution_review_packet_blocks_handoff_mismatches():
    observations = [
        _planned_observation("ldoc-contract-review-mini"),
        _planned_observation("ldoc-civil-complaint-mini"),
        _planned_observation("ldoc-defense-answer-mini"),
        _planned_observation("ldoc-lawyer-letter-mini"),
    ]
    observations[0]["observed_model"] = "gemini-2.5-pro"

    packet = LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService().build_packet(
        {"observations": observations}
    )
    review_items = {item["id"]: item for item in packet["review_items"]}

    assert packet["status"] == "blocked"
    assert packet["summary"]["archive_status"] == "blocked"
    assert packet["summary"]["handoff_status"] == "blocked"
    assert packet["summary"]["ready_for_release_packet"] is False
    assert "result-archive-review-packet-linked" in packet["blocking_check_ids"]
    assert "handoff-release-action-ready" in packet["blocking_check_ids"]
    assert review_items["execution-result-handoff"]["status"] == "blocked"
    assert "cheap-first-handoff-aligned" in review_items["execution-result-handoff"]["blocking_ids"]


def test_route_plan_execution_review_packet_rejects_raw_input_without_echoing_values():
    blocked_key_shape = "s" + "k-" + ("P" * 28)
    private_contact = "client" + "@" + "example.test"
    packet = LegalDocumentBenchmarkRoutePlanExecutionReviewPacketService().build_packet(
        {
            "observations": [_planned_observation("ldoc-contract-review-mini")],
            "headers": {"authorization": f"Bearer {blocked_key_shape}"},
            "gateway_response": {"body": f"{private_contact} raw model output"},
            "prompt": "raw legal text should not be retained",
        }
    )
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["status"] == "blocked"
    assert packet["source_summaries"]["execution_result_handoff"]["status"] == "blocked"
    assert "result-archive-review-packet-linked" in packet["blocking_check_ids"]
    assert packet["privacy_boundary"]["returns_gateway_responses"] is False
    assert blocked_key_shape not in serialized
    assert private_contact not in serialized
    assert "raw model output" not in serialized
    assert "raw legal text should not be retained" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_route_plan_execution_review_packet_route_returns_packet():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-review-packet"
    )
    assert template_response.status_code == 200
    assert template_response.json()["data"]["id"] == REVIEW_PACKET_ID
    assert template_response.json()["data"]["status"] == "review_required"

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-review-packet",
        json={"observations": [_planned_observation("ldoc-contract-review-mini")]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["summary"]["model_called"] is False
    assert payload["data"]["summary"]["ready_for_release_packet"] is True
