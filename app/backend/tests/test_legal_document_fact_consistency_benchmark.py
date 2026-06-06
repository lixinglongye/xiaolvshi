import json
import re

from services.legal_document_fact_consistency_benchmark import (
    MAX_CASES,
    LegalDocumentFactConsistencyBenchmarkService,
)


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{12,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def _passing_outputs() -> dict[str, dict]:
    suite = LegalDocumentFactConsistencyBenchmarkService().build_suite()
    outputs: dict[str, dict] = {}
    for case in suite["benchmark_cases"]:
        outputs[case["id"]] = {
            "amounts": {
                item["id"]: item["value"]
                for item in case["amount_expectations"]
            },
            "deadlines": {
                item["id"]: item["value"]
                for item in case["deadline_expectations"]
            },
            "facts": list(case["required_fact_ids"]),
        }
    return outputs


def test_fact_consistency_suite_is_laptop_safe_and_metadata_only():
    suite = LegalDocumentFactConsistencyBenchmarkService().build_suite()
    serialized = json.dumps(suite, ensure_ascii=False)

    assert suite["status"] == "ready"
    assert suite["summary"]["case_count"] == MAX_CASES
    assert suite["summary"]["check_count"] == 5
    assert suite["summary"]["model_calls"] == "not_required"
    assert suite["summary"]["network_access"] == "disabled"
    assert suite["summary"]["external_datasets"] == "disabled"
    assert suite["resource_policy"]["profile"] == "laptop_safe"
    assert suite["privacy_boundary"]["metadata_only"] is True
    assert suite["privacy_boundary"]["returns_raw_document_text"] is False
    assert suite["privacy_boundary"]["returns_generated_text"] is False
    assert suite["privacy_boundary"]["returns_credentials"] is False
    assert all("snippet" not in case for case in suite["benchmark_cases"])
    assert all("document_text" not in case for case in suite["benchmark_cases"])

    for pattern in SENSITIVE_PATTERNS:
        assert re.search(pattern, serialized) is None


def test_fact_consistency_default_evaluation_is_not_run():
    result = LegalDocumentFactConsistencyBenchmarkService().evaluate_outputs()

    assert result["status"] == "not_run"
    assert result["score"] == 0
    assert result["case_count"] == MAX_CASES
    assert result["not_run_case_count"] == MAX_CASES
    assert result["blocking_case_ids"] == []
    assert result["privacy_boundary"]["model_calls"] is False
    assert result["privacy_boundary"]["network_called"] is False


def test_fact_consistency_passes_structured_outputs():
    result = LegalDocumentFactConsistencyBenchmarkService().evaluate_outputs(_passing_outputs())

    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["passed_case_count"] == MAX_CASES
    assert result["amount_mismatch_count"] == 0
    assert result["deadline_mismatch_count"] == 0
    assert result["contradiction_count"] == 0
    assert result["raw_input_field_count"] == 0
    assert result["blocking_case_ids"] == []
    assert all(item["metric_scores"]["amount_consistency"] == 100 for item in result["case_results"])
    assert all(item["metric_scores"]["deadline_consistency"] == 100 for item in result["case_results"])


def test_fact_consistency_blocks_amount_and_deadline_mismatch():
    outputs = _passing_outputs()
    outputs["fact-lease-arrears-mini"]["amounts"]["arrears_total"] = 9000
    outputs["fact-lease-arrears-mini"]["deadlines"]["cure_due_date"] = "2026-04-11"

    result = LegalDocumentFactConsistencyBenchmarkService().evaluate_outputs(outputs)
    row = next(item for item in result["case_results"] if item["case_id"] == "fact-lease-arrears-mini")

    assert result["status"] == "fail"
    assert "fact-lease-arrears-mini" in result["blocking_case_ids"]
    assert result["amount_mismatch_count"] == 1
    assert result["deadline_mismatch_count"] == 1
    assert row["status"] == "fail"
    assert row["hard_consistency_block"] is True
    assert row["mismatched_amount_ids"] == ["arrears_total"]
    assert row["mismatched_deadline_ids"] == ["cure_due_date"]
    assert "amount-mismatch" in row["reason_codes"]
    assert "deadline-mismatch" in row["reason_codes"]


def test_fact_consistency_blocks_contradictory_facts():
    outputs = _passing_outputs()
    outputs["fact-service-contract-sla-mini"]["facts"].append("fault_response_sla_complete")

    result = LegalDocumentFactConsistencyBenchmarkService().evaluate_outputs(outputs)
    row = next(item for item in result["case_results"] if item["case_id"] == "fact-service-contract-sla-mini")

    assert result["status"] == "fail"
    assert result["contradiction_count"] == 1
    assert row["contradiction_pair_ids"] == ["sla-present-vs-gap"]
    assert row["hard_consistency_block"] is True
    assert "fact-contradiction" in row["reason_codes"]


def test_fact_consistency_rejects_raw_or_sensitive_input_without_echoing_it():
    outputs = _passing_outputs()
    outputs["fact-maintenance-settlement-mini"]["generated_text"] = "contact 13812345678 with sk-example-secret-value-123456"
    outputs["fact-maintenance-settlement-mini"]["facts"].append("release_effective_immediately")

    result = LegalDocumentFactConsistencyBenchmarkService().evaluate_outputs(outputs)
    serialized = json.dumps(result, ensure_ascii=False)
    row = next(item for item in result["case_results"] if item["case_id"] == "fact-maintenance-settlement-mini")

    assert result["status"] == "fail"
    assert row["raw_input_field_count"] == 1
    assert row["hard_consistency_block"] is True
    assert "raw-or-sensitive-input-rejected" in row["reason_codes"]
    assert "contact 138" not in serialized
    assert "13812345678" not in serialized
    assert "sk-example" not in serialized


def test_fact_consistency_route_returns_suite_and_evaluation():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/document-fact-consistency")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["status"] == "ready"
    assert get_payload["data"]["summary"]["case_count"] == MAX_CASES

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-fact-consistency",
        json=_passing_outputs(),
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["success"] is True
    assert post_payload["data"]["status"] == "pass"
    assert post_payload["data"]["score"] == 100
