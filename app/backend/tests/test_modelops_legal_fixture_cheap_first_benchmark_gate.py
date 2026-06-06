import json
import re

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def _passing_observations() -> dict[str, dict]:
    template = LegalReviewBenchmarkService().build_fixture_smoke_template()
    return {
        fixture["id"]: {
            "route": fixture["expected_routes"][0],
            "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
        }
        for fixture in template["fixtures"]
    }


def _passing_document_outputs() -> dict[str, dict]:
    suite = LegalDocumentBenchmarkSuiteService().build_suite()
    return {
        case["id"]: {
            "sections": {section: "present" for section in case["required_sections"]},
            "citations": case["expected_citations"],
            "risk_labels": case["expected_risk_labels"],
            "pii_findings": [],
        }
        for case in suite["benchmark_cases"]
    }


def _passing_fact_consistency_outputs() -> dict[str, dict]:
    suite = LegalDocumentFactConsistencyBenchmarkService().build_suite()
    return {
        case["id"]: {
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
        for case in suite["benchmark_cases"]
    }


def test_legal_fixture_cheap_first_gate_is_not_run_and_metadata_only_by_default():
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate()
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["status"] == "not_run"
    assert gate["summary"]["selected_fixture_count"] == 3
    assert gate["summary"]["not_run_count"] == 3
    assert gate["summary"]["document_benchmark_status"] == "not_run"
    assert gate["summary"]["document_benchmark_case_count"] == 6
    assert gate["summary"]["document_benchmark_not_run_case_count"] == 6
    assert gate["summary"]["fact_consistency_status"] == "not_run"
    assert gate["summary"]["fact_consistency_case_count"] == 4
    assert gate["summary"]["fact_consistency_not_run_case_count"] == 4
    assert gate["summary"]["default_change_evidence_allowed"] is False
    assert gate["document_benchmark_summary"]["raw_document_snippets_returned"] is False
    assert gate["document_benchmark_summary"]["raw_candidate_text_returned"] is False
    assert gate["fact_consistency_summary"]["raw_document_text_returned"] is False
    assert gate["fact_consistency_summary"]["raw_candidate_text_returned"] is False
    assert gate["summary"]["raw_fixture_text_returned"] is False
    assert gate["summary"]["raw_model_output_returned"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["routing_policy"]["gateway_call_allowed"] is False
    assert gate["routing_policy"]["document_benchmark_required_for_default_change"] is True
    assert gate["routing_policy"]["fact_consistency_required_for_default_change"] is True
    assert all(row["gate_status"] == "not_run" for row in gate["gate_rows"])
    assert all(row["gate_status"] == "not_run" for row in gate["document_benchmark_rows"])
    assert all(row["gate_status"] == "not_run" for row in gate["fact_consistency_rows"])
    assert all(row["raw_fixture_text_returned"] is False for row in gate["gate_rows"])
    assert all(row["raw_document_snippet_returned"] is False for row in gate["document_benchmark_rows"])
    assert all(row["raw_candidate_text_returned"] is False for row in gate["document_benchmark_rows"])
    assert "input_excerpt" not in serialized
    assert "output_text" not in serialized
    assert "generated_text" not in serialized
    assert "货款32000元" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_legal_fixture_cheap_first_gate_requires_document_benchmark_before_default_evidence():
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(
        {
            "observations": _passing_observations(),
        }
    )

    assert gate["status"] == "ready_with_watchlist"
    assert gate["summary"]["pass_count"] == 3
    assert gate["summary"]["document_benchmark_status"] == "not_run"
    assert gate["summary"]["fact_consistency_status"] == "not_run"
    assert gate["summary"]["default_change_evidence_allowed"] is False
    assert gate["summary"]["default_evidence_allowed_count"] == 0
    assert gate["default_evidence_fixture_ids"] == []
    assert "Run the legal document benchmark suite" in gate["recommended_actions"][0]


def test_legal_fixture_cheap_first_gate_allows_passing_fixture_and_document_evidence():
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
            "run_metadata": {
                "fixture-service-agreement-small": {
                    "phase": "cheap_first",
                    "model": "gemini-2.5-flash-lite",
                    "estimated_cost_usd": 0.00009,
                }
            },
        }
    )

    assert gate["status"] == "ready"
    assert gate["summary"]["evaluated_fixture_count"] == 3
    assert gate["summary"]["pass_count"] == 3
    assert gate["summary"]["default_evidence_allowed_count"] == 3
    assert gate["summary"]["default_change_evidence_allowed"] is True
    assert gate["summary"]["document_benchmark_status"] == "pass"
    assert gate["summary"]["document_benchmark_score"] == 100
    assert gate["summary"]["document_benchmark_passed_case_count"] == 6
    assert gate["summary"]["fact_consistency_status"] == "pass"
    assert gate["summary"]["fact_consistency_score"] == 100
    assert gate["summary"]["fact_consistency_passed_case_count"] == 4
    assert gate["summary"]["raw_input_field_count"] >= 1
    assert gate["default_evidence_fixture_ids"] == [
        "fixture-service-agreement-small",
        "fixture-lease-dispute-notice-small",
        "fixture-low-text-pdf-page-small",
    ]
    assert all(row["default_change_evidence_allowed"] is True for row in gate["gate_rows"])
    assert all(row["gate_status"] == "pass" for row in gate["document_benchmark_rows"])
    assert all(row["gate_status"] == "pass" for row in gate["fact_consistency_rows"])
    assert all("known-low-cost-gemini-cheap-first" in row["reason_codes"] for row in gate["gate_rows"])


def test_legal_fixture_cheap_first_gate_blocks_failed_selected_fixture():
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(
        {
            "observations": {
                "fixture-service-agreement-small": {
                    "route": "fast",
                    "output_text": "risk_matrix",
                }
            }
        }
    )
    rows = {row["fixture_id"]: row for row in gate["gate_rows"]}

    assert gate["status"] == "blocked"
    assert gate["summary"]["blocked_count"] == 1
    assert "fixture-service-agreement-small" in gate["blocking_fixture_ids"]
    assert rows["fixture-service-agreement-small"]["gate_status"] == "blocked"
    assert "high-priority-fixture-improvement" in rows["fixture-service-agreement-small"]["reason_codes"]
    assert rows["fixture-service-agreement-small"]["release_action"] == "block_default_change_until_selected_fixture_is_fixed"
    assert rows["fixture-lease-dispute-notice-small"]["gate_status"] == "not_run"


def test_legal_fixture_cheap_first_gate_blocks_failed_document_benchmark_case():
    document_outputs = _passing_document_outputs()
    target_case = LegalDocumentBenchmarkSuiteService().build_suite()["benchmark_cases"][0]
    document_outputs[target_case["id"]]["citations"] = target_case["expected_citations"][:1]
    document_outputs[target_case["id"]]["generated_text"] = "\u8054\u7cfb 13812345678"

    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": document_outputs,
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        }
    )
    document_rows = {row["case_id"]: row for row in gate["document_benchmark_rows"]}

    assert gate["status"] == "blocked"
    assert gate["summary"]["document_benchmark_status"] == "blocked"
    assert gate["summary"]["document_benchmark_blocking_case_count"] == 1
    assert gate["summary"]["default_change_evidence_allowed"] is False
    assert target_case["id"] in gate["blocking_document_case_ids"]
    assert document_rows[target_case["id"]]["gate_status"] == "blocked"
    assert document_rows[target_case["id"]]["hard_pii_block"] is True
    assert document_rows[target_case["id"]]["missing_citation_count"] == 1
    assert "document-pii-hard-block" in document_rows[target_case["id"]]["reason_codes"]
    assert "document-benchmark-failed" in document_rows[target_case["id"]]["reason_codes"]
    serialized = json.dumps(gate, ensure_ascii=False)
    assert "generated_text" not in serialized
    assert "13812345678" not in serialized


def test_legal_fixture_cheap_first_gate_blocks_document_coverage_gaps():
    class GapCoverageService:
        def build_matrix(self):
            matrix = __import__(
                "services.legal_document_benchmark_coverage",
                fromlist=["LegalDocumentBenchmarkCoverageService"],
            ).LegalDocumentBenchmarkCoverageService().build_matrix()
            matrix["status"] = "ready_with_gaps"
            matrix["summary"]["missing_document_type_count"] = 1
            matrix["summary"]["covered_document_type_count"] = matrix["summary"]["target_document_type_count"] - 1
            matrix["missing_document_types"] = ["legal_opinion"]
            return matrix

    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService(
        document_coverage_service=GapCoverageService()
    ).build_gate(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        }
    )

    assert gate["status"] == "blocked"
    assert gate["summary"]["document_benchmark_status"] == "blocked"
    assert gate["summary"]["document_coverage_status"] == "ready_with_gaps"
    assert gate["summary"]["document_coverage_missing_type_count"] == 1
    assert gate["summary"]["default_change_evidence_allowed"] is False
    assert gate["default_change_evidence_allowed"] is False
    assert gate["default_evidence_fixture_ids"] == []


def test_legal_fixture_cheap_first_gate_blocks_failed_fact_consistency_case():
    fact_outputs = _passing_fact_consistency_outputs()
    fact_outputs["fact-lease-arrears-mini"]["amounts"]["arrears_total"] = 9000
    fact_outputs["fact-lease-arrears-mini"]["deadlines"]["cure_due_date"] = "2026-04-11"

    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": fact_outputs,
        }
    )
    rows = {row["case_id"]: row for row in gate["fact_consistency_rows"]}

    assert gate["status"] == "blocked"
    assert gate["summary"]["fact_consistency_status"] == "blocked"
    assert gate["summary"]["fact_consistency_blocking_case_count"] == 1
    assert gate["summary"]["fact_consistency_amount_mismatch_count"] == 1
    assert gate["summary"]["fact_consistency_deadline_mismatch_count"] == 1
    assert gate["summary"]["default_change_evidence_allowed"] is False
    assert gate["blocking_fact_consistency_case_ids"] == ["fact-lease-arrears-mini"]
    assert rows["fact-lease-arrears-mini"]["gate_status"] == "blocked"
    assert rows["fact-lease-arrears-mini"]["mismatched_amount_count"] == 1
    assert rows["fact-lease-arrears-mini"]["mismatched_deadline_count"] == 1
    assert "amount-mismatch" in rows["fact-lease-arrears-mini"]["reason_codes"]
    assert "deadline-mismatch" in rows["fact-lease-arrears-mini"]["reason_codes"]


def test_legal_fixture_cheap_first_gate_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["status"] == "not_run"
    assert get_payload["data"]["privacy_boundary"]["returns_raw_fixture_text"] is False

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
        json={
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        },
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["data"]["status"] == "ready"
    assert post_payload["data"]["summary"]["default_evidence_allowed_count"] == 3
    assert post_payload["data"]["document_benchmark_summary"]["status"] == "pass"
    assert post_payload["data"]["fact_consistency_summary"]["status"] == "pass"
