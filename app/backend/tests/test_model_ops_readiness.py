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
    assert result["summary"]["warning_drilldown_count"] == 1
    assert result["summary"]["p1_warning_count"] == 1
    assert result["warning_category_counts"] == {"runtime_telemetry_review": 1}
    assert result["warning_drilldown"][0]["id"] == "route-guardrails"
    assert result["warning_drilldown"][0]["warning_category"] == "runtime_telemetry_review"
    assert result["warning_drilldown"][0]["severity"] == "p1_required_review"
    assert "route telemetry" in result["warning_drilldown"][0]["next_action"].lower()
    assert result["warning_drilldown"][0]["privacy_boundary"]["metadata_only"] is True
    assert result["warning_drilldown"][0]["privacy_boundary"]["credentials_included"] is False


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
    assert result["warning_drilldown"][0]["warning_category"] == "catalog_pricing_review"
    assert "catalog" in result["warning_drilldown"][0]["next_action"].lower()


def test_model_ops_readiness_warns_on_observed_gemini_coverage_gaps():
    signals = _signals("pass")
    signals["observed_gemini_coverage_gap_queue"] = {
        "status": "review_required",
        "summary": {"warn_count": 1, "fail_count": 0, "gap_item_count": 1},
        "blocking_check_ids": [],
        "warning_check_ids": ["observed-gemini-coverage-gap"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "observed-gemini-coverage-gap-queue" in result["warning_check_ids"]
    assert "observed-gemini-coverage-gap-queue" not in result["blocking_check_ids"]
    assert result["summary"]["required_warning_count"] == 1
    assert result["warning_drilldown"][0]["source_key"] == "observed_gemini_coverage_gap_queue"
    assert result["warning_drilldown"][0]["warning_category"] == "catalog_pricing_review"
    assert "catalog" in result["warning_drilldown"][0]["next_action"].lower()


def test_model_ops_readiness_warns_on_observed_gateway_fit_matrix_review():
    signals = _signals("pass")
    signals["observed_gateway_model_fit_matrix"] = {
        "status": "review_required",
        "summary": {"warn_count": 2, "fail_count": 0, "missing_task_count": 2},
        "blocking_check_ids": [],
        "warning_check_ids": ["task-capability-coverage", "review-only-model-boundary"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "observed-gateway-model-fit-matrix" in result["warning_check_ids"]
    assert "observed-gateway-model-fit-matrix" not in result["blocking_check_ids"]
    assert result["summary"]["required_warning_count"] == 1
    assert result["warning_drilldown"][0]["source_key"] == "observed_gateway_model_fit_matrix"
    assert result["warning_drilldown"][0]["warning_category"] == "catalog_pricing_review"
    assert "catalog" in result["warning_drilldown"][0]["next_action"].lower()
    assert "test_modelops_observed_gateway_model_fit_matrix.py" in result["warning_drilldown"][0]["validation_hint"]


def test_model_ops_readiness_warns_on_runtime_explicit_model_fit_gate_review():
    signals = _signals("pass")
    signals["runtime_explicit_model_fit_gate"] = {
        "status": "review_required",
        "summary": {"warn_count": 2, "fail_count": 0, "unknown_gateway_passthrough_count": 1},
        "blocking_check_ids": [],
        "warning_check_ids": ["unknown-gateway-passthrough-visible", "explicit-over-budget-boundary"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "runtime-explicit-model-fit-gate" in result["warning_check_ids"]
    assert "runtime-explicit-model-fit-gate" not in result["blocking_check_ids"]
    assert result["summary"]["required_warning_count"] == 1
    assert result["warning_drilldown"][0]["source_key"] == "runtime_explicit_model_fit_gate"
    assert result["warning_drilldown"][0]["warning_category"] == "routing_quality_review"
    assert "quality gates" in result["warning_drilldown"][0]["next_action"].lower()
    assert "test_model_ops_runtime_explicit_model_fit_gate.py" in result["warning_drilldown"][0]["validation_hint"]


def test_model_ops_readiness_warns_on_gemini_route_preflight_review():
    signals = _signals("pass")
    signals["gemini_cheap_first_route_preflight"] = {
        "status": "review_required",
        "summary": {"warn_count": 1, "fail_count": 0, "review_variant_count": 3},
        "blocking_check_ids": [],
        "warning_check_ids": ["preview-premium-review-boundary"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "gemini-cheap-first-route-preflight" in result["warning_check_ids"]
    assert "gemini-cheap-first-route-preflight" not in result["blocking_check_ids"]
    assert result["summary"]["required_warning_count"] == 1
    assert result["warning_drilldown"][0]["source_key"] == "gemini_cheap_first_route_preflight"
    assert result["warning_drilldown"][0]["warning_category"] == "catalog_pricing_review"
    assert "catalog" in result["warning_drilldown"][0]["next_action"].lower()
    assert result["warning_drilldown"][0]["privacy_boundary"]["gateway_called"] is False


def test_model_ops_readiness_warns_on_aihub_endpoint_route_coverage_review():
    signals = _signals("pass")
    signals["aihub_endpoint_route_coverage_gate"] = {
        "status": "review_required",
        "summary": {"warn_count": 2, "fail_count": 0, "legacy_unrouted_count": 0},
        "blocking_check_ids": [],
        "warning_check_ids": ["response-route-payload-coverage", "local-catalog-coverage"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "aihub-endpoint-route-coverage-gate" in result["warning_check_ids"]
    assert "aihub-endpoint-route-coverage-gate" not in result["blocking_check_ids"]
    assert result["summary"]["required_warning_count"] == 1
    assert result["warning_drilldown"][0]["source_key"] == "aihub_endpoint_route_coverage_gate"
    assert result["warning_drilldown"][0]["warning_category"] == "routing_quality_review"
    assert "task quality gates" in result["warning_drilldown"][0]["next_action"]
    assert result["warning_drilldown"][0]["privacy_boundary"]["gateway_called"] is False


def test_model_ops_readiness_warns_on_gateway_connection_profile_review():
    signals = _signals("pass")
    signals["gateway_connection_profile"] = {
        "status": "warn",
        "summary": {"warn_count": 2, "fail_count": 0},
        "blocking_check_ids": [],
        "warning_check_ids": ["base-url-configured", "api-key-configured"],
    }

    result = ModelOpsReadinessService().evaluate(signals)

    assert result["status"] == "warn"
    assert "gateway-connection-profile" in result["warning_check_ids"]
    assert "gateway-connection-profile" not in result["blocking_check_ids"]
    assert result["warning_drilldown"][0]["source_key"] == "gateway_connection_profile"
    assert result["warning_drilldown"][0]["warning_category"] == "configuration_review"
    assert "gateway connection" in result["warning_drilldown"][0]["next_action"]
    assert "test_model_gateway_connection_profile.py" in result["warning_drilldown"][0]["validation_hint"]
    assert result["warning_drilldown"][0]["privacy_boundary"]["credentials_included"] is False


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
    assert result["summary"]["p0_warning_count"] == 1
    assert result["warning_drilldown"][0]["severity"] == "p0_blocking_required"
    assert result["warning_drilldown"][0]["warning_category"] == "cost_guardrail_review"


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
    drilldown = result["warning_drilldown"][0]
    assert drilldown["id"] == "gateway-probe-evaluation"
    assert drilldown["warning_category"] == "manual_evidence_gap"
    assert drilldown["severity"] == "p2_optional_review"
    assert "sanitized manual gateway probe evidence" in drilldown["next_action"]
    assert "test_model_gateway_probe_evaluation.py" in drilldown["validation_hint"]


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
    assert payload["model_ops_readiness"]["summary"]["warning_drilldown_count"] >= 1
    assert payload["model_ops_readiness"]["warning_category_counts"]
    assert payload["model_ops_readiness"]["warning_drilldown"]
    assert all(
        row["privacy_boundary"]["credentials_included"] is False
        for row in payload["model_ops_readiness"]["warning_drilldown"]
    )
    assert "sk-" not in str(payload["model_ops_readiness"]["warning_drilldown"])
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
    assert "catalog_candidate_impact_replay" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "gemini_newapi_alias_capability_coverage" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "observed_gemini_coverage_gap_queue" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "runtime_explicit_model_fit_gate" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert payload["observed_gemini_coverage_gap_queue"]["summary"]["configuration_written"] is False
    assert payload["observed_gemini_coverage_gap_queue"]["summary"]["gateway_called"] is False
    assert payload["runtime_explicit_model_fit_gate"]["summary"]["configuration_written"] is False
    assert payload["runtime_explicit_model_fit_gate"]["summary"]["gateway_called"] is False
    assert payload["gemini_newapi_alias_capability_coverage"]["summary"]["known_coverage_count"] >= 100
    assert payload["gemini_newapi_alias_capability_coverage"]["summary"]["gateway_called"] is False
    replay_check = next(
        check for check in payload["model_ops_readiness"]["checks"] if check["source_key"] == "catalog_candidate_impact_replay"
    )
    assert replay_check["status"] in {"pass", "warn"}
    assert payload["catalog_candidate_impact_replay"]["status"] in {"monitor_only", "ready", "review_required", "blocked"}
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
    assert "gemini_cheap_first_coverage_gate" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "gemini_cheap_first_route_preflight" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "aihub_endpoint_route_coverage_gate" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert payload["gemini_cheap_first_coverage_gate"]["summary"]["coverage_row_count"] == 8
    assert payload["gemini_cheap_first_route_preflight"]["summary"]["route_task_count"] == 10
    assert payload["gemini_cheap_first_route_preflight"]["summary"]["gateway_called"] is False
    assert payload["aihub_endpoint_route_coverage_gate"]["summary"]["endpoint_count"] == 7
    assert payload["aihub_endpoint_route_coverage_gate"]["summary"]["runtime_routed_count"] == 7
    assert payload["aihub_endpoint_route_coverage_gate"]["summary"]["legacy_unrouted_count"] == 0
    assert payload["aihub_endpoint_route_coverage_gate"]["summary"]["gateway_called"] is False
    assert payload["gemini_variant_matrix"]["summary"]["catalog_model_count"] >= 8
    assert payload["catalog_source_audit"]["summary"]["source_reference_count"] == 2
    assert payload["gateway_probe_evaluation"]["status"] == "not_run"
    assert payload["model_ops_performance_budget"]["status"] == "pass"
    assert payload["route_quality_budget"]["summary"]["cheap_start_task_count"] >= 6
    assert payload["cheap_first_release_decision"]["summary"]["required_signal_count"] == 10
    assert payload["cheap_first_escalation_budget"]["status"] == "pass"
    assert payload["failure_upgrade_budget"]["status"] == "pass"
    assert "cheap_first_escalation_budget" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert "failure_upgrade_budget" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert any(
        check["source_key"] == "model_ops_readiness"
        for check in payload["cheap_first_release_decision"]["checks"]
    )
    assert payload["default_change_queue"]["summary"]["queue_item_count"] >= 6
    assert payload["default_change_queue"]["summary"]["configuration_written"] is False
    assert "cheap_first_priority_queue" in {
        check["source_key"] for check in payload["model_ops_readiness"]["checks"]
    }
    assert payload["cheap_first_priority_queue"]["summary"]["priority_item_count"] >= 6
    assert payload["cheap_first_priority_queue"]["summary"]["configuration_written"] is False
