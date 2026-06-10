import json
import re

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import (
    LegalDocumentFactConsistencyBenchmarkService,
)
from services.legal_fixture_regression import LegalFixtureRegressionService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.model_ops_gemini_official_lifecycle_drift_gate import (
    ModelOpsGeminiOfficialLifecycleDriftGateService,
)
from services.modelops_legal_benchmark_default_promotion_bridge import (
    ModelOpsLegalBenchmarkDefaultPromotionBridgeService,
)
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)
from services.modelops_legal_fixture_cheap_first_regression_budget import (
    ModelOpsLegalFixtureCheapFirstRegressionBudgetService,
)
from services.modelops_legal_fixture_default_promotion_packet import (
    ModelOpsLegalFixtureDefaultPromotionPacketService,
)
from services.modelops_legal_fixture_evidence_handoff import ModelOpsLegalFixtureEvidenceHandoffService


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
    budget = ModelOpsLegalFixtureCheapFirstRegressionBudgetService().build_budget(
        {
            "legal_fixture_cheap_first_benchmark_gate": gate,
            "legal_fixture_cheap_first_default_promotion_packet": promotion,
            "legal_fixture_regression": regression,
            "runbook_evidence": _ready_runbook(),
        }
    )
    handoff = ModelOpsLegalFixtureEvidenceHandoffService().build_handoff(
        {
            "local_run_review": {
                "status": "ready",
                "summary": {"observed_fixture_count": 3},
                "blocking_check_ids": [],
                "warning_check_ids": [],
            },
            "cheap_first_benchmark_gate": gate,
            "default_promotion_packet": promotion,
        }
    )
    return {
        "legal_fixture_cheap_first_benchmark_gate": gate,
        "legal_fixture_cheap_first_default_promotion_packet": promotion,
        "legal_fixture_cheap_first_regression_budget": budget,
        "legal_fixture_evidence_handoff": handoff,
        "gemini_official_lifecycle_drift_gate": ModelOpsGeminiOfficialLifecycleDriftGateService().build_gate(),
    }


def test_default_promotion_bridge_defaults_to_review_required_and_metadata_only():
    bridge = ModelOpsLegalBenchmarkDefaultPromotionBridgeService().build_bridge()
    serialized = json.dumps(bridge, ensure_ascii=False)

    assert bridge["id"] == "modelops-legal-benchmark-default-promotion-bridge"
    assert bridge["status"] == "review_required"
    assert bridge["summary"]["source_count"] == 5
    assert bridge["summary"]["source_gemini_lifecycle_status"] == "review_required"
    assert bridge["summary"]["default_change_allowed_by_bridge"] is False
    assert bridge["decision"]["default_change_allowed_by_bridge"] is False
    assert bridge["decision"]["maintainer_review_required"] is True
    assert bridge["privacy_boundary"]["metadata_only"] is True
    assert bridge["privacy_boundary"]["network_called"] is False
    assert bridge["privacy_boundary"]["configuration_written"] is False
    assert bridge["claim_boundary"]["automatic_default_change_claimed"] is False
    assert bridge["claim_boundary"]["legal_advice_claimed"] is False
    assert "output_text" not in serialized
    assert "generated_text" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_default_promotion_bridge_promotes_ready_sources_to_maintainer_review_without_config_write():
    bridge = ModelOpsLegalBenchmarkDefaultPromotionBridgeService().build_bridge(_ready_sources())
    checks = {check["id"]: check for check in bridge["checks"]}

    assert bridge["status"] == "review_required"
    assert bridge["summary"]["promotion_row_count"] == 3
    assert bridge["summary"]["promotion_ready_count"] == 3
    assert bridge["summary"]["promotion_blocked_count"] == 0
    assert bridge["summary"]["source_benchmark_gate_status"] == "ready"
    assert bridge["summary"]["source_default_promotion_packet_status"] == "ready_for_maintainer_review"
    assert bridge["summary"]["source_regression_budget_status"] == "review_required"
    assert bridge["summary"]["blocked_default_count"] == 0
    assert checks["legal-fixture-benchmark-ready"]["status"] == "pass"
    assert checks["default-promotion-packet-ready"]["status"] == "pass"
    assert checks["regression-budget-not-blocked"]["status"] == "pass"
    assert checks["gemini-lifecycle-defaults-not-blocked"]["status"] == "pass"
    assert bridge["decision"]["current_cheap_first_defaults_allowed"] is True
    assert bridge["decision"]["configuration_change_allowed"] is False
    assert bridge["decision"]["gateway_call_allowed"] is False
    assert all(row["default_change_allowed_by_bridge"] is False for row in bridge["promotion_rows"])


def test_default_promotion_bridge_blocks_lifecycle_default_drift():
    sources = _ready_sources()
    sources["gemini_official_lifecycle_drift_gate"] = ModelOpsGeminiOfficialLifecycleDriftGateService().build_gate(
        {
            "official_lifecycle_snapshot": [
                {
                    "model_id": "gemini-2.5-flash-lite",
                    "official_lifecycle": "deprecated",
                    "default_policy": "blocked_from_defaults",
                    "default_allowed_for_high_frequency": False,
                }
            ]
        }
    )

    bridge = ModelOpsLegalBenchmarkDefaultPromotionBridgeService().build_bridge(sources)
    checks = {check["id"]: check for check in bridge["checks"]}

    assert bridge["status"] == "blocked"
    assert checks["gemini-lifecycle-defaults-not-blocked"]["status"] == "fail"
    assert "gemini-lifecycle-defaults-not-blocked" in bridge["blocking_check_ids"]
    assert bridge["summary"]["blocked_default_count"] == 4
    assert bridge["decision"]["current_cheap_first_defaults_allowed"] is False


def test_default_promotion_bridge_redacts_sensitive_payload_and_blocks_regressions():
    sources = _ready_sources()
    budget = dict(sources["legal_fixture_cheap_first_regression_budget"])
    budget["status"] = "blocked"
    budget["blocking_check_ids"] = ["fixture-regression-pass"]
    budget["summary"] = {**budget["summary"], "blocked_count": 1, "regressed_fixture_count": 1}
    sources["legal_fixture_cheap_first_regression_budget"] = budget
    sources["raw_output"] = "RAW_PRIVATE_RESULT_SHOULD_NOT_LEAK"
    sources["api_key"] = "sk-" + ("b" * 24)

    bridge = ModelOpsLegalBenchmarkDefaultPromotionBridgeService().build_bridge(sources)
    serialized = json.dumps(bridge, ensure_ascii=False)

    assert bridge["status"] == "blocked"
    assert "regression-budget-not-blocked" in bridge["blocking_check_ids"]
    assert bridge["summary"]["raw_input_field_count"] >= 2
    assert "RAW_PRIVATE_RESULT_SHOULD_NOT_LEAK" not in serialized
    assert "sk-" + ("b" * 24) not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_default_promotion_bridge_aihub_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-benchmark-default-promotion-bridge")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()["data"]
    assert direct_payload["id"] == "modelops-legal-benchmark-default-promotion-bridge"
    assert direct_payload["summary"]["network_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/legal-benchmark-default-promotion-bridge",
        json={
            "gemini_official_lifecycle_drift_gate": {
                "status": "blocked",
                "summary": {"blocked_default_count": 1},
                "blocking_check_ids": ["synthetic-lifecycle-block"],
                "warning_check_ids": [],
            }
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["legal_benchmark_default_promotion_bridge"]["id"]
        == "modelops-legal-benchmark-default-promotion-bridge"
    )
    assert any(
        check["source_key"] == "legal_benchmark_default_promotion_bridge"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
    assert any(
        check["source_key"] == "legal_benchmark_default_promotion_bridge"
        for check in models_payload["cheap_first_release_decision"]["checks"]
    )
