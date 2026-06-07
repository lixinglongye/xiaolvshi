import json
import re

from services.gemini_model_variant_matrix import GeminiModelVariantMatrixService
from services.gemini_newapi_cheap_first_calibration import GeminiNewapiCheapFirstCalibrationService
from services.model_catalog_source_audit import ModelCatalogSourceAuditService
from services.model_failure_upgrade_budget import ModelFailureUpgradeBudgetService
from services.model_ops_cheap_first_escalation_budget import ModelOpsCheapFirstEscalationBudgetService
from services.model_ops_cheap_first_release_decision import ModelOpsCheapFirstReleaseDecisionService
from services.model_ops_gemini_cheap_first_route_preflight import ModelOpsGeminiCheapFirstRoutePreflightService
from services.model_ops_performance_budget import ModelOpsPerformanceBudgetService
from services.model_price_refresh_monitor import ModelPriceRefreshMonitorService
from services.model_route_quality_budget import ModelRouteQualityBudgetService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")


def _current_signals() -> dict:
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
    assert checks["catalog_source_audit"]["status"] == "warn"
    assert checks["gemini_cheap_first_route_preflight"]["status"] == "warn"
    assert "catalog-source-audit-review" in decision["warning_check_ids"]
    assert "gemini-cheap-first-route-preflight-review" in decision["warning_check_ids"]
    assert decision["privacy_boundary"]["network_called"] is False
    assert decision["claim_boundary"]["public_benchmark_scores_included"] is False
    assert decision["claim_boundary"]["twenty_four_hour_completion_claimed"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_cheap_first_release_decision_passes_when_all_source_signals_pass():
    signals = {key: _pass_signal() for key in (
        "cheap_first_calibration",
        "model_ops_readiness",
        "gemini_variant_matrix",
        "gemini_cheap_first_route_preflight",
        "catalog_source_audit",
        "route_quality_budget",
        "cheap_first_escalation_budget",
        "failure_upgrade_budget",
        "price_refresh_monitor",
        "model_ops_performance_budget",
    )}

    decision = ModelOpsCheapFirstReleaseDecisionService().build_decision(signals)

    assert decision["status"] == "pass"
    assert decision["release_decision"]["status"] == "ready"
    assert decision["summary"]["passing_signal_count"] == 10
    assert decision["summary"]["default_promotion_blocked"] is False
    assert decision["blocking_check_ids"] == []
    assert decision["warning_check_ids"] == []


def test_cheap_first_release_decision_blocks_when_required_source_signal_fails():
    signals = {key: _pass_signal() for key in (
        "cheap_first_calibration",
        "model_ops_readiness",
        "gemini_variant_matrix",
        "gemini_cheap_first_route_preflight",
        "catalog_source_audit",
        "route_quality_budget",
        "cheap_first_escalation_budget",
        "failure_upgrade_budget",
        "price_refresh_monitor",
        "model_ops_performance_budget",
    )}
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
    assert decision_payload["data"]["summary"]["required_signal_count"] == 10

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["cheap_first_release_decision"]["summary"]["required_signal_count"] == 10
    assert any(
        check["source_key"] == "model_ops_readiness"
        for check in payload["cheap_first_release_decision"]["checks"]
    )
    assert any(
        check["source_key"] == "gemini_cheap_first_route_preflight"
        for check in payload["cheap_first_release_decision"]["checks"]
    )
