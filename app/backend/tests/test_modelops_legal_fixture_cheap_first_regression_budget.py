import json
import re

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import (
    LegalDocumentFactConsistencyBenchmarkService,
)
from services.legal_fixture_regression import LegalFixtureRegressionService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)
from services.modelops_legal_fixture_cheap_first_regression_budget import (
    ModelOpsLegalFixtureCheapFirstRegressionBudgetService,
)
from services.modelops_legal_fixture_default_promotion_packet import (
    ModelOpsLegalFixtureDefaultPromotionPacketService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
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


def _passing_fact_outputs() -> dict[str, dict]:
    suite = LegalDocumentFactConsistencyBenchmarkService().build_suite()
    return {
        case["id"]: {
            "amounts": {item["id"]: item["value"] for item in case["amount_expectations"]},
            "deadlines": {item["id"]: item["value"] for item in case["deadline_expectations"]},
            "facts": list(case["required_fact_ids"]),
        }
        for case in suite["benchmark_cases"]
    }


def _passing_metadata(cost: float = 0.0001) -> dict[str, dict]:
    return {
        fixture_id: {
            "phase": "cheap_first",
            "model": "gemini-2.5-flash-lite",
            "estimated_cost_usd": cost,
        }
        for fixture_id in _passing_observations()
    }


def _ready_runbook() -> dict:
    return {
        "id": "small-legal-document-benchmark-runbook-evidence",
        "status": "ready",
        "summary": {
            "ready_evidence_row_count": 15,
            "blocked_evidence_row_count": 0,
            "review_required_evidence_row_count": 0,
            "max_parallel_requests": 1,
        },
        "blocking_check_ids": [],
        "warning_check_ids": [],
    }


def _ready_sources() -> dict:
    observations = _passing_observations()
    gate_payload = {
        "observations": observations,
        "document_benchmark_outputs": _passing_document_outputs(),
        "document_fact_consistency_outputs": _passing_fact_outputs(),
    }
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(gate_payload)
    promotion = ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet({"source_gate": gate})
    regression = LegalFixtureRegressionService().build_comparison(
        {
            "baseline": {"observations": observations, "run_metadata": _passing_metadata()},
            "current": {"observations": observations, "run_metadata": _passing_metadata()},
        }
    )
    return {
        "legal_fixture_cheap_first_benchmark_gate": gate,
        "legal_fixture_cheap_first_default_promotion_packet": promotion,
        "legal_fixture_regression": regression,
        "runbook_evidence": _ready_runbook(),
    }


def test_regression_budget_default_is_not_ready_and_metadata_only():
    budget = ModelOpsLegalFixtureCheapFirstRegressionBudgetService().build_budget()
    serialized = json.dumps(budget, ensure_ascii=False)

    assert budget["id"] == "modelops-legal-fixture-cheap-first-regression-budget"
    assert budget["status"] == "not_ready"
    assert budget["summary"]["source_regression_status"] == "not_run"
    assert budget["summary"]["source_gate_status"] == "not_run"
    assert budget["summary"]["source_runbook_status"] == "review_required"
    assert budget["summary"]["max_parallel_requests"] == 1
    assert budget["decision"]["default_change_allowed_by_budget"] is False
    assert budget["decision"]["configuration_change_allowed"] is False
    assert budget["privacy_boundary"]["returns_raw_fixture_text"] is False
    assert budget["privacy_boundary"]["returns_raw_model_output"] is False
    assert all(row["budget_status"] == "not_run" for row in budget["budget_rows"])
    assert "output_text" not in serialized
    assert "generated_text" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_regression_budget_promotes_passing_sources_to_maintainer_review_without_writing_config():
    budget = ModelOpsLegalFixtureCheapFirstRegressionBudgetService().build_budget(_ready_sources())

    assert budget["status"] == "review_required"
    assert budget["summary"]["fixture_budget_row_count"] == 3
    assert budget["summary"]["pass_count"] == 3
    assert budget["summary"]["blocked_count"] == 0
    assert budget["summary"]["source_regression_status"] == "pass"
    assert budget["summary"]["source_gate_status"] == "ready"
    assert budget["summary"]["source_promotion_packet_status"] == "ready_for_maintainer_review"
    assert budget["summary"]["source_runbook_status"] == "ready"
    assert budget["decision"]["current_cheap_first_default_allowed"] is True
    assert budget["decision"]["default_change_allowed_by_budget"] is False
    assert budget["decision"]["gateway_call_allowed"] is False
    assert all(row["budget_status"] == "pass" for row in budget["budget_rows"])
    assert all(row["default_change_allowed_by_budget"] is False for row in budget["budget_rows"])
    assert any(check["id"] == "default-promotion-packet-reviewed" for check in budget["checks"])


def test_regression_budget_blocks_fixture_regression_without_echoing_raw_values():
    observations = _passing_observations()
    current = dict(observations)
    current["fixture-service-agreement-small"] = {
        "route": "fast",
        "output_text": "RAW_PRIVATE_RESULT_SHOULD_NOT_LEAK",
        "raw_response": {"content": "secret sk-" + ("b" * 24)},
    }
    sources = _ready_sources()
    sources["legal_fixture_regression"] = LegalFixtureRegressionService().build_comparison(
        {
            "baseline": {"observations": observations, "run_metadata": _passing_metadata()},
            "current": {"observations": current, "run_metadata": _passing_metadata(0.0002)},
        }
    )
    sources["raw_output"] = "RAW_PRIVATE_RESULT_SHOULD_NOT_LEAK"

    budget = ModelOpsLegalFixtureCheapFirstRegressionBudgetService().build_budget(sources)
    serialized = json.dumps(budget, ensure_ascii=False)

    assert budget["status"] == "blocked"
    assert "fixture-regression-pass" in budget["blocking_check_ids"]
    assert budget["summary"]["regressed_fixture_count"] == 1
    assert budget["summary"]["raw_input_field_count"] >= 1
    assert any(row["fixture_id"] == "fixture-service-agreement-small" for row in budget["budget_rows"])
    target = next(row for row in budget["budget_rows"] if row["fixture_id"] == "fixture-service-agreement-small")
    assert target["budget_status"] == "blocked"
    assert "regression-new_escalation_required" in target["reason_codes"]
    assert "RAW_PRIVATE_RESULT_SHOULD_NOT_LEAK" not in serialized
    assert "sk-" + ("b" * 24) not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_regression_budget_aihub_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-fixture-cheap-first-regression-budget")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()
    assert direct_payload["success"] is True
    assert direct_payload["data"]["summary"]["max_parallel_requests"] == 1
    assert direct_payload["data"]["decision"]["default_change_allowed_by_budget"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    budget = models_payload["legal_fixture_cheap_first_regression_budget"]
    assert budget["summary"]["source_gate_status"] == "not_run"
    assert budget["summary"]["source_regression_status"] == "not_run"
    assert budget["privacy_boundary"]["network_called"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(budget, ensure_ascii=False))
