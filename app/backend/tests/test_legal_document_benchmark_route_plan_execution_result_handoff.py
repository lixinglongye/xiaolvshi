import json
import re

from services.legal_document_benchmark_route_plan_execution_result_handoff import (
    HANDOFF_ID,
    LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|access[_-]?token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def _planned_observation(case_id: str, *, phase: str = "primary") -> dict:
    service = LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService()
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


def test_route_plan_execution_result_handoff_builds_review_template():
    handoff = LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService().build_handoff()

    assert handoff["id"] == HANDOFF_ID
    assert handoff["status"] == "review_required"
    assert handoff["summary"]["readiness_status"] == "ready"
    assert handoff["summary"]["archive_status"] == "not_run"
    assert handoff["summary"]["observation_count"] == 0
    assert handoff["summary"]["ready_for_release_evidence"] is False
    assert handoff["summary"]["release_action"] == "collect_manual_observations_before_release_evidence"
    assert handoff["summary"]["model_called"] is False
    assert handoff["summary"]["network_called"] is False
    assert handoff["summary"]["benchmark_execution_claimed"] is False
    assert handoff["release_evidence_packet"]["records_maintainer_approval"] is False
    assert handoff["release_evidence_packet"]["writes_release_record"] is False
    assert "manual-observations-present" in handoff["warning_check_ids"]
    assert not SENSITIVE_PATTERN.search(json.dumps(handoff, ensure_ascii=False))


def test_route_plan_execution_result_handoff_accepts_ready_archive_rows():
    handoff = LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService().build_handoff(
        {
            "observations": [
                _planned_observation("ldoc-contract-review-mini"),
                _planned_observation("ldoc-civil-complaint-mini", phase="precheck"),
            ]
        }
    )
    rows = {row["case_id"]: row for row in handoff["handoff_rows"]}

    assert handoff["status"] == "ready"
    assert handoff["summary"]["archive_status"] == "ready"
    assert handoff["summary"]["ready_for_release_evidence"] is True
    assert handoff["summary"]["release_action"] == "attach_to_release_evidence"
    assert handoff["summary"]["attachable_row_count"] == 2
    assert handoff["summary"]["cheap_first_aligned_count"] == 2
    assert rows["ldoc-contract-review-mini"]["can_attach_to_release"] is True
    assert rows["ldoc-civil-complaint-mini"]["phase"] == "precheck"
    assert rows["ldoc-civil-complaint-mini"]["handoff_action"] == "attach_row_as_metadata_only_evidence"
    assert handoff["release_evidence_packet"]["ready_for_release_evidence"] is True


def test_route_plan_execution_result_handoff_blocks_archive_mismatches():
    observations = [
        _planned_observation("ldoc-contract-review-mini"),
        _planned_observation("ldoc-civil-complaint-mini"),
        _planned_observation("ldoc-defense-answer-mini"),
        _planned_observation("ldoc-lawyer-letter-mini"),
    ]
    observations[0]["observed_model"] = "gemini-2.5-pro"

    handoff = LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService().build_handoff(
        {"observations": observations}
    )

    assert handoff["status"] == "blocked"
    assert handoff["summary"]["archive_status"] == "blocked"
    assert handoff["summary"]["ready_for_release_evidence"] is False
    assert "execution-result-archive-ready" in handoff["blocking_check_ids"]
    assert "cheap-first-handoff-aligned" in handoff["blocking_check_ids"]
    assert "low-resource-envelope-preserved" in handoff["blocking_check_ids"]
    assert handoff["handoff_rows"][0]["handoff_status"] == "blocked"
    assert handoff["handoff_rows"][0]["can_attach_to_release"] is False


def test_route_plan_execution_result_handoff_rejects_raw_input_without_echoing_values():
    blocked_key_shape = "s" + "k-" + ("H" * 28)
    private_contact = "client" + "@" + "example.test"
    handoff = LegalDocumentBenchmarkRoutePlanExecutionResultHandoffService().build_handoff(
        {
            "observations": [_planned_observation("ldoc-contract-review-mini")],
            "headers": {"authorization": f"Bearer {blocked_key_shape}"},
            "gateway_response": {"body": f"{private_contact} raw model output"},
            "prompt": "raw legal text should not be retained",
        }
    )
    serialized = json.dumps(handoff, ensure_ascii=False)

    assert handoff["status"] == "blocked"
    assert handoff["summary"]["forbidden_payload_field_count"] >= 3
    assert "metadata-only-boundary-preserved" in handoff["blocking_check_ids"]
    assert handoff["privacy_boundary"]["returns_gateway_responses"] is False
    assert blocked_key_shape not in serialized
    assert private_contact not in serialized
    assert "raw model output" not in serialized
    assert "raw legal text should not be retained" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_route_plan_execution_result_handoff_route_returns_handoff():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-handoff"
    )
    assert template_response.status_code == 200
    assert template_response.json()["data"]["id"] == HANDOFF_ID
    assert template_response.json()["data"]["status"] == "review_required"

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-handoff",
        json={"observations": [_planned_observation("ldoc-contract-review-mini")]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["summary"]["model_called"] is False
    assert payload["data"]["summary"]["ready_for_release_evidence"] is True
