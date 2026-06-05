from services.model_gateway_probe_evaluation import model_gateway_probe_evaluation_registry
from services.model_ops_readiness import MODEL_OPS_COMPONENTS, ModelOpsReadinessService


def _signals(status: str = "pass"):
    payload = {}
    for component in MODEL_OPS_COMPONENTS:
        if component.source_key == "budget_policy":
            payload[component.source_key] = {"task_decisions": [{"task": "fast"}]}
        else:
            payload[component.source_key] = {
                "status": status,
                "summary": {"warn_count": 0, "fail_count": 0},
                "blocking_check_ids": [],
                "warning_check_ids": [],
            }
    return payload


def test_model_ops_readiness_passes_when_all_components_are_ready():
    result = ModelOpsReadinessService().evaluate(_signals("pass"))

    assert result["status"] == "pass"
    assert result["release_recommendation"] == "ready_for_model_ops_release"
    assert result["summary"]["component_count"] == len(MODEL_OPS_COMPONENTS)
    assert result["summary"]["required_component_count"] == len([component for component in MODEL_OPS_COMPONENTS if component.required])
    assert result["summary"]["optional_component_count"] == 1
    assert result["summary"]["required_warning_count"] == 0
    assert result["summary"]["optional_review_count"] == 0
    assert result["summary"]["required_failure_count"] == 0
    assert result["summary"]["optional_failure_count"] == 0
    assert result["blocking_check_ids"] == []
    assert "sk-" not in str(result)


def test_model_ops_readiness_warns_on_warning_component():
    signals = _signals("pass")
    signals["route_guardrails"] = {
        "status": "warn",
        "summary": {"warn_count": 1, "fail_count": 0},
        "blocking_check_ids": [],
        "warning_check_ids": ["unknown-price-route-count"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert result["release_recommendation"] == "maintainer_review_required"
    assert "route-guardrails" in result["warning_check_ids"]
    assert result["summary"]["required_warning_count"] == 1
    assert result["summary"]["optional_review_count"] == 0


def test_model_ops_readiness_warns_on_review_required_gemini_variant_matrix():
    signals = _signals("pass")
    signals["gemini_variant_matrix"] = {
        "status": "review_required",
        "summary": {"warn_count": 0, "fail_count": 0},
        "blocking_check_ids": [],
        "warning_check_ids": ["catalog-unpriced-models"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "gemini-variant-matrix" in result["warning_check_ids"]
    assert "gemini-variant-matrix" not in result["blocking_check_ids"]
    assert result["summary"]["required_warning_count"] == 1


def test_model_ops_readiness_fails_on_blocking_component():
    signals = _signals("pass")
    signals["cost_guardrails"] = {
        "status": "fail",
        "summary": {"warn_count": 0, "fail_count": 1},
        "blocking_check_ids": ["actual-cost-budget"],
        "warning_check_ids": [],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "fail"
    assert result["release_recommendation"] == "blocked"
    assert "cost-guardrails" in result["blocking_check_ids"]
    assert result["summary"]["required_failure_count"] == 1
    assert result["summary"]["optional_failure_count"] == 0


def test_model_ops_readiness_fails_when_required_signal_is_missing():
    signals = _signals("pass")
    signals.pop("runtime_router")

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "fail"
    assert "runtime-router" in result["blocking_check_ids"]


def test_model_ops_readiness_warns_when_optional_probe_evaluation_is_missing():
    signals = _signals("pass")
    signals.pop("gateway_probe_evaluation")

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "gateway-probe-evaluation" in result["warning_check_ids"]
    assert "gateway-probe-evaluation" not in result["blocking_check_ids"]
    assert result["summary"]["required_warning_count"] == 0
    assert result["summary"]["optional_review_count"] == 1
    assert result["summary"]["optional_failure_count"] == 0
    probe_check = next(check for check in result["checks"] if check["id"] == "gateway-probe-evaluation")
    assert probe_check["required"] is False


def test_model_ops_readiness_warns_on_failed_optional_probe_when_supplied():
    signals = _signals("pass")
    signals["gateway_probe_evaluation"] = {
        "status": "fail",
        "summary": {"warn_count": 0, "fail_count": 1},
        "blocking_check_ids": ["sanitized-payload-fields"],
        "warning_check_ids": [],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "gateway-probe-evaluation" in result["warning_check_ids"]
    assert "gateway-probe-evaluation" not in result["blocking_check_ids"]
    assert result["summary"]["required_failure_count"] == 0
    assert result["summary"]["optional_review_count"] == 1
    assert result["summary"]["optional_failure_count"] == 1
    assert any("Gateway probe evaluation" in action for action in result["recommended_actions"])


def test_model_ops_route_includes_readiness():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    model_gateway_probe_evaluation_registry.clear()
    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["model_ops_readiness"]["status"] in {"pass", "warn", "fail"}
    assert payload["model_ops_readiness"]["summary"]["optional_component_count"] >= 1
    assert payload["model_ops_readiness"]["summary"]["optional_review_count"] >= 1
    assert payload["model_ops_readiness"]["checks"]
    assert "price_refresh_monitor" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "gateway_probe_evaluation" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "gemini_variant_matrix" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "catalog_source_audit" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "model_ops_performance_budget" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "route_quality_budget" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "cheap_first_canary_promotion_decision" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "cheap_first_canary_approval_packet" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "cheap_first_canary_rollback_drill" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "cheap_first_canary_change_manifest" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "cheap_first_canary_observation" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert payload["gemini_variant_matrix"]["summary"]["catalog_model_count"] >= 8
    assert payload["catalog_source_audit"]["summary"]["source_reference_count"] == 2
    assert payload["gateway_probe_evaluation"]["status"] == "not_run"
    assert payload["model_ops_performance_budget"]["status"] == "pass"
    assert payload["route_quality_budget"]["summary"]["cheap_start_task_count"] >= 6
    assert payload["cheap_first_release_decision"]["summary"]["required_signal_count"] == 7
    assert any(
        check["source_key"] == "model_ops_readiness"
        for check in payload["cheap_first_release_decision"]["checks"]
    )
    assert payload["default_change_queue"]["summary"]["queue_item_count"] >= 6
    assert payload["default_change_queue"]["summary"]["configuration_written"] is False
