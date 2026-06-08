import json
import re

from services.gemini_model_variant_matrix import GeminiModelVariantMatrixService
from services.gemini_newapi_cheap_first_calibration import GeminiNewapiCheapFirstCalibrationService
from services.model_catalog_source_audit import ModelCatalogSourceAuditService
from services.model_failure_upgrade_budget import ModelFailureUpgradeBudgetService
from services.model_ops_cheap_first_escalation_budget import ModelOpsCheapFirstEscalationBudgetService
from services.model_ops_cheap_first_release_decision import (
    REQUIRED_SIGNAL_KEYS,
    ModelOpsCheapFirstReleaseDecisionService,
)
from services.model_ops_legal_benchmark_risk_bridge import ModelOpsLegalBenchmarkRiskBridgeService
from services.model_ops_gemini_cheap_first_route_preflight import ModelOpsGeminiCheapFirstRoutePreflightService
from services.model_ops_performance_budget import ModelOpsPerformanceBudgetService
from services.model_ops_user_need_release_bridge import ModelOpsUserNeedReleaseBridgeService
from services.model_price_refresh_monitor import ModelPriceRefreshMonitorService
from services.model_route_quality_budget import ModelRouteQualityBudgetService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)
from services.modelops_legal_fixture_default_promotion_packet import (
    ModelOpsLegalFixtureDefaultPromotionPacketService,
)


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _current_signals() -> dict:
    legal_fixture_gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate()
    legal_promotion_packet = ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet(
        {"source_gate": legal_fixture_gate}
    )
    signals = {
        "cheap_first_calibration": GeminiNewapiCheapFirstCalibrationService().build_calibration(),
        "gemini_variant_matrix": GeminiModelVariantMatrixService().build_matrix(),
        "gemini_cheap_first_route_preflight": ModelOpsGeminiCheapFirstRoutePreflightService().build_preflight(),
        "catalog_source_audit": ModelCatalogSourceAuditService().build_audit(),
        "route_quality_budget": ModelRouteQualityBudgetService().build_budget(),
        "cheap_first_escalation_budget": ModelOpsCheapFirstEscalationBudgetService().build_budget(),
        "failure_upgrade_budget": ModelFailureUpgradeBudgetService().build_decision(),
        "price_refresh_monitor": ModelPriceRefreshMonitorService().build_monitor(),
        "model_ops_performance_budget": ModelOpsPerformanceBudgetService().build_budget(),
        "legal_fixture_cheap_first_benchmark_gate": legal_fixture_gate,
        "legal_fixture_cheap_first_default_promotion_packet": legal_promotion_packet,
        "legal_benchmark_risk_bridge": ModelOpsLegalBenchmarkRiskBridgeService().build_bridge(),
        "user_need_release_bridge": ModelOpsUserNeedReleaseBridgeService().build_bridge(),
    }
    signals["model_ops_readiness"] = {
        "status": "warn",
        "summary": {"blocking_count": 0, "warning_count": 2},
        "blocking_check_ids": [],
        "warning_check_ids": ["catalog-source-audit", "gemini-variant-matrix"],
    }
    return signals


def _pass_signal() -> dict:
    return {
        "status": "pass",
        "summary": {"blocking_count": 0, "warning_count": 0},
        "blocking_check_ids": [],
        "warning_check_ids": [],
    }


def _all_pass_signals() -> dict:
    return {key: _pass_signal() for key in REQUIRED_SIGNAL_KEYS}


def test_cheap_first_release_decision_requires_review_for_current_catalog_watchlist():
    decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(_current_signals())
    checks = {check["source_key"]: check for check in decision["checks"]}
    serialized = json.dumps(decision, ensure_ascii=False)

    assert decision["status"] == "review_required"
    assert decision["release_decision"]["status"] == "review_required"
    assert decision["summary"]["default_promotion_blocked"] is False
    assert decision["summary"]["maintainer_review_required"] is True
    assert "catalog_source_audit" in checks
    assert "gemini_cheap_first_route_preflight" in checks
    assert "legal_fixture_cheap_first_benchmark_gate" in checks
    assert "legal_fixture_cheap_first_default_promotion_packet" in checks
    assert "legal_benchmark_risk_bridge" in checks
    assert "user_need_release_bridge" in checks
    assert checks["catalog_source_audit"]["status"] == "warn"
    assert checks["gemini_cheap_first_route_preflight"]["status"] == "warn"
    assert checks["legal_fixture_cheap_first_benchmark_gate"]["status"] == "warn"
    assert checks["legal_fixture_cheap_first_default_promotion_packet"]["status"] == "warn"
    assert checks["legal_benchmark_risk_bridge"]["status"] == "warn"
    assert checks["user_need_release_bridge"]["status"] == "warn"
    assert "catalog-source-audit-review" in decision["warning_check_ids"]
    assert "gemini-cheap-first-route-preflight-review" in decision["warning_check_ids"]
    assert "legal-fixture-cheap-first-benchmark-gate" in decision["warning_check_ids"]
    assert "legal-fixture-default-promotion-packet" in decision["warning_check_ids"]
    assert "legal-benchmark-risk-bridge" in decision["warning_check_ids"]
    assert "user-need-release-bridge" in decision["warning_check_ids"]
    assert checks["user_need_release_bridge"]["source_summary"]["need_count"] >= 7
    assert checks["user_need_release_bridge"]["source_summary"]["default_change_review_need_count"] >= 1
    assert decision["privacy_boundary"]["network_called"] is False
    assert decision["claim_boundary"]["public_benchmark_scores_included"] is False
    assert decision["claim_boundary"]["twenty_four_hour_completion_claimed"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_cheap_first_release_decision_passes_when_all_source_signals_pass():
    signals = _all_pass_signals()

    decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(signals)

    assert decision["status"] == "pass"
    assert decision["release_decision"]["status"] == "ready"
    assert decision["summary"]["passing_signal_count"] == len(REQUIRED_SIGNAL_KEYS)
    assert decision["summary"]["required_signal_count"] == len(REQUIRED_SIGNAL_KEYS)
    assert decision["summary"]["default_promotion_blocked"] is False
    assert decision["blocking_check_ids"] == []
    assert decision["warning_check_ids"] == []


def test_cheap_first_release_decision_blocks_when_required_source_signal_fails():
    signals = _all_pass_signals()
    signals["route_quality_budget"] = {
        "status": "fail",
        "summary": {"blocking_count": 1, "warning_count": 0},
        "blocking_check_ids": ["runtime-default-capability-gap"],
        "warning_check_ids": [],
    }

    decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(signals)

    assert decision["status"] == "fail"
    assert decision["release_decision"]["status"] == "blocked"
    assert decision["summary"]["default_promotion_blocked"] is True
    assert "route-quality-budget-review" in decision["blocking_check_ids"]
    assert "runtime-default-capability-gap" in decision["source_blocking_ids"]


def test_cheap_first_release_decision_blocks_failed_user_need_release_bridge():
    signals = _all_pass_signals()
    signals["user_need_release_bridge"] = {
        "status": "blocked",
        "summary": {
            "need_count": 1,
            "blocked_need_count": 1,
            "default_change_blocked_need_count": 1,
            "high_priority_route_blocked_count": 1,
        },
        "blocking_check_ids": ["modelops-user-need-release-synthetic-need"],
        "warning_check_ids": [],
    }

    decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(signals)
    check = next(check for check in decision["checks"] if check["source_key"] == "user_need_release_bridge")

    assert decision["status"] == "fail"
    assert decision["release_decision"]["status"] == "blocked"
    assert "user-need-release-bridge" in decision["blocking_check_ids"]
    assert "modelops-user-need-release-synthetic-need" in decision["source_blocking_ids"]
    assert check["source_summary"]["need_count"] == 1
    assert check["source_summary"]["default_change_blocked_need_count"] == 1
    assert check["source_summary"]["high_priority_route_blocked_count"] == 1


def test_cheap_first_release_decision_reviews_user_need_release_bridge_warnings():
    signals = _all_pass_signals()
    signals["user_need_release_bridge"] = {
        "status": "review_required",
        "summary": {
            "need_count": 2,
            "review_required_need_count": 2,
            "default_change_review_need_count": 2,
            "public_benchmark_review_need_count": 1,
            "premium_exception_review_need_count": 1,
        },
        "blocking_check_ids": [],
        "warning_check_ids": ["modelops-user-need-release-public-benchmark"],
    }

    decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(signals)
    check = next(check for check in decision["checks"] if check["source_key"] == "user_need_release_bridge")

    assert decision["status"] == "review_required"
    assert decision["release_decision"]["status"] == "review_required"
    assert decision["summary"]["default_promotion_blocked"] is False
    assert "user-need-release-bridge" in decision["warning_check_ids"]
    assert check["source_summary"]["default_change_review_need_count"] == 2
    assert check["source_summary"]["public_benchmark_review_need_count"] == 1
    assert check["source_summary"]["premium_exception_review_need_count"] == 1


def test_cheap_first_release_decision_blocks_failed_legal_fixture_gate():
    signals = _all_pass_signals()
    signals["legal_fixture_cheap_first_benchmark_gate"] = {
        "status": "blocked",
        "summary": {
            "blocking_count": 1,
            "blocked_count": 1,
            "document_benchmark_blocking_case_count": 1,
            "fact_consistency_blocking_case_count": 1,
        },
        "blocking_check_ids": ["fixture-smoke-failed"],
        "warning_check_ids": [],
    }

    decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(signals)
    check = next(
        check
        for check in decision["checks"]
        if check["source_key"] == "legal_fixture_cheap_first_benchmark_gate"
    )

    assert decision["status"] == "fail"
    assert decision["release_decision"]["status"] == "blocked"
    assert "legal-fixture-cheap-first-benchmark-gate" in decision["blocking_check_ids"]
    assert "fixture-smoke-failed" in decision["source_blocking_ids"]
    assert check["source_summary"]["blocked_count"] == 1
    assert check["source_summary"]["document_benchmark_blocking_case_count"] == 1
    assert check["source_summary"]["fact_consistency_blocking_case_count"] == 1


def test_cheap_first_release_decision_route_and_model_ops_payload_include_readiness_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    decision_response = client.get("/api/v1/aihub/models/cheap-first-release-decision")
    assert decision_response.status_code == 200
    decision_payload = decision_response.json()
    assert decision_payload["success"] is True
    assert decision_payload["data"]["summary"]["required_signal_count"] == len(REQUIRED_SIGNAL_KEYS)

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["cheap_first_release_decision"]["summary"]["required_signal_count"] == len(REQUIRED_SIGNAL_KEYS)
    source_keys = {check["source_key"] for check in payload["cheap_first_release_decision"]["checks"]}
    assert any(
        check["source_key"] == "model_ops_readiness"
        for check in payload["cheap_first_release_decision"]["checks"]
    )
    assert any(
        check["source_key"] == "gemini_cheap_first_route_preflight"
        for check in payload["cheap_first_release_decision"]["checks"]
    )
    assert "legal_fixture_cheap_first_benchmark_gate" in source_keys
    assert "legal_fixture_cheap_first_default_promotion_packet" in source_keys
    assert "legal_benchmark_risk_bridge" in source_keys
    assert "user_need_release_bridge" in source_keys
    assert payload["user_need_release_bridge"]["id"] == "modelops-user-need-release-bridge"
    assert payload["user_need_gemini_route_coverage"]["id"] == "user-need-gemini-route-coverage"
    assert payload["user_need_implementation_priority_queue"]["summary"]["network_access"] == "disabled"
