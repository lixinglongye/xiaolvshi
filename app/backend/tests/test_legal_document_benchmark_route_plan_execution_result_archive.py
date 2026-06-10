import json
import re

from services.legal_document_benchmark_route_plan_execution_result_archive import (
    ARCHIVE_ID,
    LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|password|secret|api[_-]?key|authorization|access[_-]?token|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def _planned_observation(case_id: str, *, phase: str = "primary") -> dict:
    service = LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService()
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


def test_route_plan_execution_result_archive_builds_not_run_template():
    archive = LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService().build_archive()

    assert archive["id"] == ARCHIVE_ID
    assert archive["status"] == "not_run"
    assert archive["summary"]["readiness_status"] == "ready"
    assert archive["summary"]["manual_execution_ready"] is True
    assert archive["summary"]["observation_count"] == 0
    assert archive["summary"]["recommended_fixture_limit"] == 3
    assert archive["summary"]["max_parallel_model_requests"] == 1
    assert archive["summary"]["model_called"] is False
    assert archive["summary"]["network_called"] is False
    assert archive["summary"]["benchmark_execution_claimed"] is False
    assert archive["privacy_boundary"]["returns_model_outputs"] is False
    assert archive["claim_boundary"]["benchmark_executed_by_service"] is False
    assert "manual-observations-supplied" in archive["warning_check_ids"]
    assert not SENSITIVE_PATTERN.search(json.dumps(archive, ensure_ascii=False))


def test_route_plan_execution_result_archive_accepts_sanitized_manual_observations():
    archive = LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService().build_archive(
        {
            "observations": [
                _planned_observation("ldoc-contract-review-mini"),
                _planned_observation("ldoc-civil-complaint-mini", phase="precheck"),
            ]
        }
    )
    rows = {row["case_id"]: row for row in archive["archive_rows"]}

    assert archive["status"] == "ready"
    assert archive["summary"]["observation_count"] == 2
    assert archive["summary"]["ready_observation_count"] == 2
    assert archive["summary"]["matched_route_case_count"] == 2
    assert archive["summary"]["cheap_first_aligned_count"] == 2
    assert archive["summary"]["observed_cost_usd_sum"] == 0.0004
    assert rows["ldoc-contract-review-mini"]["release_action"] == "accept_as_metadata_only_release_evidence"
    assert rows["ldoc-civil-complaint-mini"]["phase"] == "precheck"
    assert rows["ldoc-civil-complaint-mini"]["expected_model"] == "gemini-2.5-flash-lite"
    assert archive["archive_policy"]["records_maintainer_approval"] is False


def test_route_plan_execution_result_archive_blocks_model_mismatch_and_limit_overrun():
    observations = [
        _planned_observation("ldoc-contract-review-mini"),
        _planned_observation("ldoc-civil-complaint-mini"),
        _planned_observation("ldoc-defense-answer-mini"),
        _planned_observation("ldoc-lawyer-letter-mini"),
    ]
    observations[0]["observed_model"] = "gemini-2.5-pro"

    archive = LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService().build_archive(
        {"observations": observations}
    )
    first_row = archive["archive_rows"][0]

    assert archive["status"] == "blocked"
    assert first_row["result_status"] == "blocked"
    assert "observed_model_mismatch" in first_row["reason_codes"]
    assert "manual-observations-within-fixture-limit" in archive["blocking_check_ids"]
    assert "observed-cheap-first-model-alignment" in archive["blocking_check_ids"]
    assert first_row["release_action"] == "block_until_observed_model_matches_route_plan"


def test_route_plan_execution_result_archive_rejects_raw_payload_without_echoing_values():
    blocked_key_shape = "s" + "k-" + ("R" * 28)
    private_contact = "client" + "@" + "example.test"
    archive = LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService().build_archive(
        {
            "observations": [_planned_observation("ldoc-contract-review-mini")],
            "headers": {"authorization": f"Bearer {blocked_key_shape}"},
            "gateway_response": {"body": f"{private_contact} raw model output"},
            "prompt": "raw legal text should not be retained",
        }
    )
    serialized = json.dumps(archive, ensure_ascii=False)

    assert archive["status"] == "blocked"
    assert archive["summary"]["forbidden_payload_field_count"] >= 3
    assert "sanitized-result-metadata-only" in archive["blocking_check_ids"]
    assert archive["privacy_boundary"]["returns_gateway_responses"] is False
    assert blocked_key_shape not in serialized
    assert private_contact not in serialized
    assert "raw model output" not in serialized
    assert "raw legal text should not be retained" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_route_plan_execution_result_archive_route_returns_archive():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template_response = client.get(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-archive"
    )
    assert template_response.status_code == 200
    assert template_response.json()["data"]["id"] == ARCHIVE_ID
    assert template_response.json()["data"]["status"] == "not_run"

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-route-plan/execution-result-archive",
        json={"observations": [_planned_observation("ldoc-contract-review-mini")]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"
    assert payload["data"]["summary"]["model_called"] is False
    assert payload["data"]["summary"]["observation_count"] == 1
