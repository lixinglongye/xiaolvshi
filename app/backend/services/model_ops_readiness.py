from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReadinessComponent:
    id: str
    label: str
    category: str
    source_key: str
    required: bool = True


MODEL_OPS_COMPONENTS: tuple[ReadinessComponent, ...] = (
    ReadinessComponent("configuration-audit", "Model configuration audit", "configuration", "model_configuration_audit"),
    ReadinessComponent(
        "default-template-audit",
        "Default template alignment",
        "configuration",
        "default_template_audit",
    ),
    ReadinessComponent("default-optimization", "Default optimization plan", "configuration", "default_optimization"),
    ReadinessComponent(
        "default-recommendation-snapshot",
        "Default recommendation snapshot",
        "configuration",
        "default_recommendation_snapshot",
    ),
    ReadinessComponent("gateway-compatibility", "Gateway compatibility", "configuration", "gateway_compatibility"),
    ReadinessComponent(
        "gateway-connection-profile",
        "Gateway connection profile",
        "configuration",
        "gateway_connection_profile",
    ),
    ReadinessComponent(
        "gateway-runtime-configuration",
        "Gateway runtime configuration",
        "configuration",
        "gateway_runtime_configuration",
    ),
    ReadinessComponent("gateway-health-plan", "Gateway health plan", "configuration", "gateway_health_plan"),
    ReadinessComponent("gemini-variant-matrix", "Gemini variant matrix", "configuration", "gemini_variant_matrix"),
    ReadinessComponent(
        "observed-gemini-model-intake-queue",
        "Observed Gemini model intake queue",
        "configuration",
        "observed_gemini_model_intake_queue",
    ),
    ReadinessComponent(
        "observed-gemini-coverage-gap-queue",
        "Observed Gemini coverage gap queue",
        "configuration",
        "observed_gemini_coverage_gap_queue",
    ),
    ReadinessComponent(
        "observed-gateway-model-fit-matrix",
        "Observed gateway model fit matrix",
        "configuration",
        "observed_gateway_model_fit_matrix",
    ),
    ReadinessComponent(
        "gemini-newapi-alias-capability-coverage",
        "Gemini/NewAPI alias capability coverage",
        "configuration",
        "gemini_newapi_alias_capability_coverage",
    ),
    ReadinessComponent(
        "gemini-newapi-model-selector",
        "Gemini/NewAPI cheap-first model selector",
        "configuration",
        "gemini_newapi_model_selector",
    ),
    ReadinessComponent(
        "gemini-newapi-selector-replay",
        "Gemini/NewAPI selector replay",
        "configuration",
        "gemini_newapi_selector_replay",
    ),
    ReadinessComponent(
        "catalog-candidate-patch-plan",
        "Model catalog candidate patch plan",
        "configuration",
        "catalog_candidate_patch_plan",
    ),
    ReadinessComponent(
        "catalog-candidate-impact-replay",
        "Model catalog candidate impact replay",
        "configuration",
        "catalog_candidate_impact_replay",
    ),
    ReadinessComponent("catalog-source-audit", "Gemini catalog source audit", "configuration", "catalog_source_audit"),
    ReadinessComponent(
        "gemini-official-cheap-first-source-review",
        "Gemini official cheap-first source review",
        "configuration",
        "gemini_official_cheap_first_source_review",
    ),
    ReadinessComponent(
        "gemini-official-model-family-roadmap-evidence",
        "Gemini official model family roadmap evidence",
        "configuration",
        "gemini_official_model_family_roadmap_evidence",
    ),
    ReadinessComponent(
        "gemini-official-lifecycle-drift-gate",
        "Gemini official lifecycle drift gate",
        "configuration",
        "gemini_official_lifecycle_drift_gate",
    ),
    ReadinessComponent(
        "gemini-embedding-cheap-first-preflight",
        "Gemini embedding cheap-first preflight",
        "configuration",
        "gemini_embedding_cheap_first_preflight",
    ),
    ReadinessComponent(
        "gateway-probe-evaluation",
        "Gateway probe evaluation",
        "manual_evidence",
        "gateway_probe_evaluation",
        required=False,
    ),
    ReadinessComponent(
        "gateway-probe-runbook-gate",
        "Gateway probe runbook gate",
        "manual_evidence",
        "gateway_probe_runbook_gate",
        required=False,
    ),
    ReadinessComponent("lifecycle-policy", "Gemini lifecycle policy", "configuration", "lifecycle_policy"),
    ReadinessComponent(
        "gemini-cheap-first-coverage-gate",
        "Gemini cheap-first coverage gate",
        "configuration",
        "gemini_cheap_first_coverage_gate",
    ),
    ReadinessComponent(
        "gemini-cheap-first-route-preflight",
        "Gemini cheap-first route preflight",
        "configuration",
        "gemini_cheap_first_route_preflight",
    ),
    ReadinessComponent(
        "gemini-research-refresh-gate",
        "Gemini research refresh gate",
        "configuration",
        "gemini_research_refresh_gate",
    ),
    ReadinessComponent(
        "aihub-endpoint-route-coverage-gate",
        "AIHub endpoint route coverage gate",
        "routing",
        "aihub_endpoint_route_coverage_gate",
    ),
    ReadinessComponent(
        "aihub-media-speech-default-catalog-gate",
        "AIHub media/speech default catalog gate",
        "routing",
        "aihub_media_speech_default_catalog_gate",
    ),
    ReadinessComponent(
        "aihub-media-runtime-compatibility-gate",
        "AIHub media runtime compatibility gate",
        "routing",
        "aihub_media_runtime_compatibility_gate",
    ),
    ReadinessComponent(
        "gentxt-routing-guard",
        "AIHub gentxt routing guard",
        "routing",
        "gentxt_routing_guard",
    ),
    ReadinessComponent("budget-policy", "Budget policy", "routing", "budget_policy"),
    ReadinessComponent("capability-matrix", "Capability matrix", "routing", "capability_matrix"),
    ReadinessComponent("runtime-router", "Runtime router", "routing", "runtime_router"),
    ReadinessComponent(
        "runtime-explicit-model-fit-gate",
        "Runtime explicit model fit gate",
        "routing",
        "runtime_explicit_model_fit_gate",
    ),
    ReadinessComponent("reasoning-policy", "Reasoning policy", "routing", "reasoning_policy"),
    ReadinessComponent("request-policy", "Request policy", "routing", "request_policy"),
    ReadinessComponent(
        "gateway-request-compatibility-gate",
        "Gateway request compatibility gate",
        "routing",
        "gateway_request_compatibility_gate",
    ),
    ReadinessComponent(
        "request-execution-preflight",
        "Request execution preflight",
        "routing",
        "request_execution_preflight",
    ),
    ReadinessComponent(
        "request-execution-observation-gate",
        "Request execution observation gate",
        "routing",
        "request_execution_observation_gate",
    ),
    ReadinessComponent("request-cost-bounds", "Request cost bounds", "routing", "request_cost_bounds"),
    ReadinessComponent("cache-policy", "Cache policy", "routing", "cache_policy"),
    ReadinessComponent("callsite-audit", "Callsite audit", "code_audit", "callsite_audit"),
    ReadinessComponent("route-telemetry", "Route telemetry", "runtime_evidence", "route_telemetry"),
    ReadinessComponent(
        "route-telemetry-repository",
        "Route telemetry repository",
        "runtime_evidence",
        "route_telemetry_repository",
    ),
    ReadinessComponent(
        "route-telemetry-ops-summary",
        "Route telemetry ops summary",
        "runtime_evidence",
        "route_telemetry_ops_summary",
    ),
    ReadinessComponent(
        "route-telemetry-triage",
        "Route telemetry triage queue",
        "runtime_evidence",
        "route_telemetry_triage",
    ),
    ReadinessComponent(
        "route-telemetry-remediation",
        "Route telemetry remediation plan",
        "runtime_evidence",
        "route_telemetry_remediation",
    ),
    ReadinessComponent(
        "route-telemetry-result-archive",
        "Route telemetry result archive",
        "runtime_evidence",
        "route_telemetry_result_archive",
    ),
    ReadinessComponent("route-guardrails", "Route guardrails", "runtime_evidence", "route_guardrails"),
    ReadinessComponent(
        "route-quality-budget",
        "Cheap-first route quality budget",
        "routing",
        "route_quality_budget",
    ),
    ReadinessComponent("routing-replay", "Routing replay", "simulation", "routing_replay"),
    ReadinessComponent("fallback-chains", "Fallback chains", "resilience", "fallback_chains"),
    ReadinessComponent("escalation-policy", "Escalation policy", "resilience", "escalation_policy"),
    ReadinessComponent(
        "failure-upgrade-budget",
        "Failure upgrade budget",
        "resilience",
        "failure_upgrade_budget",
    ),
    ReadinessComponent("cost-forecast", "Cost forecast", "cost", "cost_forecast"),
    ReadinessComponent("cost-guardrails", "Cost guardrails", "cost", "cost_guardrails"),
    ReadinessComponent(
        "cheap-first-calibration",
        "Gemini/NewAPI cheap-first calibration",
        "cost",
        "cheap_first_calibration",
    ),
    ReadinessComponent(
        "price-refresh-monitor",
        "Gemini/NewAPI price refresh monitor",
        "cost",
        "price_refresh_monitor",
    ),
    ReadinessComponent(
        "cheap-first-escalation-budget",
        "Cheap-first escalation budget",
        "cost",
        "cheap_first_escalation_budget",
    ),
    ReadinessComponent(
        "cheap-first-cascade-research-gate",
        "Cheap-first cascade research gate",
        "release_evidence",
        "cheap_first_cascade_research_gate",
    ),
    ReadinessComponent(
        "model-ops-performance-budget",
        "ModelOps performance budget",
        "runtime_evidence",
        "model_ops_performance_budget",
    ),
    ReadinessComponent(
        "legal-micro-benchmark-preflight",
        "Legal micro benchmark preflight",
        "release_evidence",
        "legal_micro_benchmark_preflight",
    ),
    ReadinessComponent(
        "legal-fixture-evidence-handoff",
        "Legal fixture evidence handoff",
        "release_evidence",
        "legal_fixture_evidence_handoff",
    ),
    ReadinessComponent(
        "legal-fixture-cheap-first-regression-budget",
        "Legal fixture cheap-first regression budget",
        "release_evidence",
        "legal_fixture_cheap_first_regression_budget",
    ),
    ReadinessComponent(
        "legal-benchmark-default-promotion-bridge",
        "Legal benchmark default-promotion bridge",
        "release_evidence",
        "legal_benchmark_default_promotion_bridge",
    ),
    ReadinessComponent(
        "legal-benchmark-default-promotion-checklist",
        "Legal benchmark default-promotion checklist",
        "release_evidence",
        "legal_benchmark_default_promotion_checklist",
    ),
    ReadinessComponent(
        "legal-benchmark-default-promotion-signoff-packet",
        "Legal benchmark default-promotion signoff packet",
        "release_evidence",
        "legal_benchmark_default_promotion_signoff_packet",
    ),
    ReadinessComponent(
        "legal-benchmark-default-promotion-execution-handoff",
        "Legal benchmark default-promotion execution handoff",
        "release_evidence",
        "legal_benchmark_default_promotion_execution_handoff",
    ),
    ReadinessComponent(
        "legal-benchmark-default-promotion-observation-gate",
        "Legal benchmark default-promotion observation gate",
        "release_evidence",
        "legal_benchmark_default_promotion_observation_gate",
    ),
    ReadinessComponent(
        "user-need-release-bridge",
        "User-need release bridge",
        "release_evidence",
        "user_need_release_bridge",
    ),
    ReadinessComponent(
        "user-need-cheap-first-handoff",
        "User-need cheap-first handoff",
        "release_evidence",
        "user_need_cheap_first_handoff",
    ),
    ReadinessComponent(
        "cheap-first-release-decision",
        "Cheap-first release decision",
        "release_evidence",
        "cheap_first_release_decision",
    ),
    ReadinessComponent(
        "default-change-queue",
        "Default change queue",
        "release_evidence",
        "default_change_queue",
    ),
    ReadinessComponent(
        "cheap-first-priority-queue",
        "Cheap-first priority queue",
        "release_evidence",
        "cheap_first_priority_queue",
    ),
    ReadinessComponent(
        "gemini-default-change-review",
        "Gemini default change review",
        "release_evidence",
        "gemini_default_change_review",
    ),
    ReadinessComponent(
        "gemini-default-cost-impact",
        "Gemini default cost impact",
        "release_evidence",
        "gemini_default_cost_impact",
    ),
    ReadinessComponent(
        "cheap-first-canary-plan",
        "Cheap-first canary plan",
        "release_evidence",
        "cheap_first_canary_plan",
    ),
    ReadinessComponent(
        "cheap-first-canary-observation",
        "Cheap-first canary observation review",
        "release_evidence",
        "cheap_first_canary_observation",
    ),
    ReadinessComponent(
        "cheap-first-canary-promotion-decision",
        "Cheap-first canary promotion decision",
        "release_evidence",
        "cheap_first_canary_promotion_decision",
    ),
    ReadinessComponent(
        "cheap-first-canary-approval-packet",
        "Cheap-first canary approval packet",
        "release_evidence",
        "cheap_first_canary_approval_packet",
    ),
    ReadinessComponent(
        "cheap-first-canary-rollback-drill",
        "Cheap-first canary rollback drill",
        "release_evidence",
        "cheap_first_canary_rollback_drill",
    ),
    ReadinessComponent(
        "cheap-first-canary-change-manifest",
        "Cheap-first canary change manifest",
        "release_evidence",
        "cheap_first_canary_change_manifest",
    ),
    ReadinessComponent(
        "cheap-first-maintainer-execution-checklist",
        "Cheap-first maintainer execution checklist",
        "release_evidence",
        "cheap_first_maintainer_execution_checklist",
    ),
)


class ModelOpsReadinessService:
    """Aggregate model-operation signals into one release-oriented readiness result."""

    def evaluate(self, signals: dict[str, Any]) -> dict[str, Any]:
        checks = [self._evaluate_component(component, signals.get(component.source_key)) for component in MODEL_OPS_COMPONENTS]
        status = self._status(checks)
        required_checks = [check for check in checks if check["required"]]
        optional_checks = [check for check in checks if not check["required"]]
        blocking = [check for check in checks if check["status"] == "fail" and check["required"]]
        warnings = [check for check in checks if check["status"] == "warn" or (check["status"] == "fail" and not check["required"])]
        warning_drilldown = self._warning_drilldown(checks)
        return {
            "status": status,
            "release_recommendation": self._release_recommendation(status),
            "method": {
                "type": "aggregate-model-ops-readiness",
                "notes": [
                    "Aggregates existing model configuration, routing, telemetry, replay, fallback, and cost controls.",
                    "Does not store prompts, documents, file names, API keys, users, emails, or raw model output.",
                    "Required fail states block model-ops release readiness; warn states require maintainer review.",
                ],
            },
            "summary": {
                "component_count": len(checks),
                "required_component_count": len(required_checks),
                "optional_component_count": len(optional_checks),
                "pass_count": sum(1 for check in checks if check["status"] == "pass"),
                "warn_count": len(warnings),
                "fail_count": sum(1 for check in checks if check["status"] == "fail"),
                "required_warning_count": sum(1 for check in required_checks if check["status"] == "warn"),
                "optional_review_count": sum(1 for check in optional_checks if check["status"] != "pass"),
                "required_failure_count": sum(1 for check in required_checks if check["status"] == "fail"),
                "optional_failure_count": sum(1 for check in optional_checks if check["status"] == "fail"),
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
                "warning_drilldown_count": len(warning_drilldown),
                "p0_warning_count": sum(1 for item in warning_drilldown if item["severity"] == "p0_blocking_required"),
                "p1_warning_count": sum(1 for item in warning_drilldown if item["severity"] == "p1_required_review"),
                "p2_warning_count": sum(1 for item in warning_drilldown if item["severity"] == "p2_optional_review"),
            },
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "warning_category_counts": self._warning_category_counts(warning_drilldown),
            "warning_drilldown": warning_drilldown,
            "recommended_actions": self._recommended_actions(checks),
        }

    def _evaluate_component(self, component: ReadinessComponent, value: Any) -> dict[str, Any]:
        data = value if isinstance(value, dict) else {}
        status = self._component_status(component, data)
        return {
            "id": component.id,
            "label": component.label,
            "category": component.category,
            "source_key": component.source_key,
            "required": component.required,
            "status": status,
            "reason": self._reason(component, data, status),
            "blocking_ids": _list(data.get("blocking_check_ids")),
            "warning_ids": _list(data.get("warning_check_ids")),
        }

    def _component_status(self, component: ReadinessComponent, data: dict[str, Any]) -> str:
        if not data:
            if component.category == "release_evidence":
                return "warn"
            return "fail" if component.required else "warn"
        if component.source_key == "budget_policy":
            return "pass" if _list(data.get("task_decisions")) else "fail"
        value = str(data.get("status") or "").strip().lower()
        if value in {"pass", "ready", "ok", "success"}:
            return "pass"
        if value in {
            "advance_next_batch",
            "approval_ready",
            "drill_ready",
            "manifest_ready",
            "monitor_only",
            "ready_for_external_change",
            "ready_for_external_execution",
        }:
            return "pass"
        if value in {
            "warn",
            "warning",
            "manual_review",
            "review_required",
            "needs_catalog_review",
            "needs_review",
            "hold_for_review",
            "approval_blocked",
            "drill_blocked",
            "manifest_blocked",
            "not_ready",
            "not_supplied",
        }:
            return "warn"
        if value == "not_run" and not component.required:
            return "warn"
        if value in {"fail", "failed", "blocked", "error", "rollback_required", "rollback_review_required"}:
            return "fail"
        return "fail" if component.required else "warn"

    def _reason(self, component: ReadinessComponent, data: dict[str, Any], status: str) -> str:
        if not data:
            if component.required:
                return f"{component.label} is missing from the model operations payload."
            return f"{component.label} is optional manual evidence and has not been supplied."
        blocking_ids = _list(data.get("blocking_check_ids"))
        warning_ids = _list(data.get("warning_check_ids"))
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        if status == "fail":
            if blocking_ids:
                return f"{component.label} has blocking checks: {', '.join(blocking_ids)}."
            if summary.get("fail_count"):
                return f"{component.label} reports {summary.get('fail_count')} failed checks."
            return f"{component.label} is not ready."
        if status == "warn":
            if warning_ids:
                return f"{component.label} has warning checks: {', '.join(warning_ids)}."
            if summary.get("warn_count"):
                return f"{component.label} reports {summary.get('warn_count')} warnings."
            return f"{component.label} needs maintainer review."
        return f"{component.label} is ready."

    def _status(self, checks: list[dict[str, Any]]) -> str:
        if any(check["status"] == "fail" and check["required"] for check in checks):
            return "fail"
        if any(check["status"] == "warn" or (check["status"] == "fail" and not check["required"]) for check in checks):
            return "warn"
        return "pass"

    def _release_recommendation(self, status: str) -> str:
        if status == "fail":
            return "blocked"
        if status == "warn":
            return "maintainer_review_required"
        return "ready_for_model_ops_release"

    def _recommended_actions(self, checks: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        for check in checks:
            if check["status"] == "pass":
                continue
            if check["status"] == "fail":
                prefix = "Resolve blocking model-ops signal" if check["required"] else "Review optional model-ops signal"
                actions.append(f"{prefix}: {check['label']}.")
            else:
                actions.append(f"Review model-ops warning: {check['label']}.")
        if not actions:
            actions.append("Model operations readiness is passing; keep all required checks attached to release evidence.")
        return actions

    def _warning_drilldown(self, checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = [self._warning_row(check) for check in checks if check["status"] != "pass"]
        return sorted(rows, key=lambda row: (-row["priority"], row["id"]))

    def _warning_row(self, check: dict[str, Any]) -> dict[str, Any]:
        category = self._warning_category(check)
        severity = self._warning_severity(check)
        return {
            "id": check["id"],
            "label": check["label"],
            "status": check["status"],
            "required": check["required"],
            "source_key": check["source_key"],
            "component_category": check["category"],
            "warning_category": category,
            "severity": severity,
            "priority": self._warning_priority(check, category, severity),
            "reason": check["reason"],
            "blocking_ids": check["blocking_ids"],
            "warning_ids": check["warning_ids"],
            "next_action": self._warning_next_action(check, category),
            "validation_hint": self._validation_hint(check, category),
            "privacy_boundary": {
                "metadata_only": True,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payloads_included": False,
                "raw_model_output_included": False,
                "credentials_included": False,
            },
        }

    def _warning_category_counts(self, warning_drilldown: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in warning_drilldown:
            category = str(row["warning_category"])
            counts[category] = counts.get(category, 0) + 1
        return dict(sorted(counts.items()))

    def _warning_severity(self, check: dict[str, Any]) -> str:
        if check["status"] == "fail" and check["required"]:
            return "p0_blocking_required"
        if check["required"]:
            return "p1_required_review"
        return "p2_optional_review"

    def _warning_priority(self, check: dict[str, Any], category: str, severity: str) -> int:
        priority = {
            "p0_blocking_required": 100,
            "p1_required_review": 70,
            "p2_optional_review": 45,
        }[severity]
        if category in {"canary_evidence_gap", "release_evidence_review", "user_need_release_review"}:
            priority += 10
        if category in {
            "catalog_pricing_review",
            "cost_guardrail_review",
            "default_recommendation_review",
            "routing_quality_review",
        }:
            priority += 5
        if check["blocking_ids"]:
            priority += min(10, len(check["blocking_ids"]) * 2)
        if check["warning_ids"]:
            priority += min(6, len(check["warning_ids"]) * 2)
        return priority

    def _warning_category(self, check: dict[str, Any]) -> str:
        source_key = str(check["source_key"])
        category = str(check["category"])
        if not check["required"]:
            return "manual_evidence_gap"
        if "canary" in source_key:
            return "canary_evidence_gap"
        if source_key == "default_recommendation_snapshot":
            return "default_recommendation_review"
        if source_key in {
            "catalog_source_audit",
            "gemini_variant_matrix",
            "observed_gemini_model_intake_queue",
            "observed_gemini_coverage_gap_queue",
            "observed_gateway_model_fit_matrix",
            "gemini_newapi_alias_capability_coverage",
            "gemini_newapi_model_selector",
            "gemini_newapi_selector_replay",
            "gemini_cheap_first_route_preflight",
            "gemini_research_refresh_gate",
            "gemini_official_model_family_roadmap_evidence",
            "gemini_official_lifecycle_drift_gate",
            "gemini_embedding_cheap_first_preflight",
            "catalog_candidate_patch_plan",
            "catalog_candidate_impact_replay",
            "price_refresh_monitor",
        }:
            return "catalog_pricing_review"
        if category == "runtime_evidence":
            return "runtime_telemetry_review"
        if source_key in {"user_need_release_bridge", "user_need_cheap_first_handoff"}:
            return "user_need_release_review"
        if source_key == "cheap_first_cascade_research_gate":
            return "cost_guardrail_review"
        if source_key in {
            "budget_policy",
            "capability_matrix",
            "runtime_router",
            "runtime_explicit_model_fit_gate",
            "reasoning_policy",
            "request_policy",
            "gateway_request_compatibility_gate",
            "request_execution_preflight",
            "request_execution_observation_gate",
            "aihub_endpoint_route_coverage_gate",
            "aihub_media_speech_default_catalog_gate",
            "aihub_media_runtime_compatibility_gate",
            "request_cost_bounds",
            "cache_policy",
            "route_quality_budget",
        }:
            return "routing_quality_review"
        if category == "cost":
            return "cost_guardrail_review"
        if category == "release_evidence":
            return "release_evidence_review"
        if category == "configuration":
            return "configuration_review"
        if category in {"resilience", "simulation"}:
            return "resilience_review"
        return "general_review"

    def _warning_next_action(self, check: dict[str, Any], warning_category: str) -> str:
        if warning_category == "manual_evidence_gap":
            return "Submit sanitized manual gateway probe evidence, or record why this optional evidence remains unavailable."
        if warning_category == "canary_evidence_gap":
            return "Attach aggregate canary observation, approval, rollback, and change-manifest evidence before promoting cheap-first defaults."
        if warning_category == "catalog_pricing_review":
            return "Review catalog, pricing, lifecycle, and alias evidence before changing Gemini/NewAPI defaults."
        if warning_category == "default_recommendation_review":
            return "Review cheap-first default recommendations, blocked default roles, and observed Gemini catalog-review models before changing environment defaults."
        if warning_category == "runtime_telemetry_review":
            return "Inspect route telemetry, triage, and remediation evidence for cheap-first routing drift."
        if warning_category == "user_need_release_review":
            return "Review user-need implementation, benchmark license, and Gemini route evidence before changing cheap-first defaults."
        if warning_category == "routing_quality_review":
            return "Review task quality gates, request budgets, and cheap-start coverage before release."
        if warning_category == "cost_guardrail_review":
            return "Review cheap-first forecast, savings, unknown-price, escalation budget, and premium-ratio signals before release."
        if warning_category == "release_evidence_review":
            return "Attach maintainer-reviewed release evidence before treating cheap-first model changes as ready."
        if warning_category == "configuration_review":
            return "Resolve configuration, gateway connection, compatibility, or template alignment warnings before release."
        if warning_category == "resilience_review":
            return "Review fallback, replay, and escalation evidence before relying on model routing resilience."
        return f"Review {check['label']} before model-ops release."

    def _validation_hint(self, check: dict[str, Any], warning_category: str) -> str:
        if warning_category == "manual_evidence_gap":
            return "python -m pytest tests/test_model_gateway_probe_evaluation.py tests/test_model_ops_readiness.py -q"
        if warning_category == "canary_evidence_gap":
            return "python -m pytest tests/test_model_ops_cheap_first_canary_observation.py tests/test_model_ops_cheap_first_canary_promotion_decision.py tests/test_model_ops_readiness.py -q"
        if warning_category == "catalog_pricing_review":
            return "python -m pytest tests/test_model_ops_gemini_official_lifecycle_drift_gate.py tests/test_model_ops_gemini_research_refresh_gate.py tests/test_gemini_newapi_model_selector.py tests/test_gemini_newapi_selector_replay.py tests/test_model_catalog_source_audit.py tests/test_model_ops_gemini_embedding_cheap_first_preflight.py tests/test_gemini_model_variant_matrix.py tests/test_modelops_observed_gateway_model_fit_matrix.py tests/test_model_price_refresh_monitor.py tests/test_model_ops_readiness.py -q"
        if warning_category == "default_recommendation_review":
            return "python -m pytest tests/test_model_default_recommendation_snapshot.py tests/test_model_default_candidate_selector.py tests/test_model_ops_readiness.py -q"
        if warning_category == "runtime_telemetry_review":
            return "python -m pytest tests/test_route_telemetry_ops_summary.py tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_remediation_plan.py tests/test_model_ops_readiness.py -q"
        if warning_category == "user_need_release_review":
            return "python -m pytest tests/test_model_ops_user_need_cheap_first_handoff.py tests/test_model_ops_user_need_release_bridge.py tests/test_user_need_implementation_priority_queue.py tests/test_user_need_gemini_route_coverage.py tests/test_model_ops_readiness.py -q"
        if warning_category == "routing_quality_review":
            return "python -m pytest tests/test_model_ops_runtime_explicit_model_fit_gate.py tests/test_model_ops_aihub_media_runtime_compatibility_gate.py tests/test_model_ops_aihub_media_speech_default_catalog_gate.py tests/test_model_route_quality_budget.py tests/test_model_request_cost_bounds.py tests/test_model_ops_readiness.py -q"
        if warning_category == "cost_guardrail_review":
            return "python -m pytest tests/test_model_cost_guardrails.py tests/test_gemini_newapi_cheap_first_calibration.py tests/test_model_ops_cheap_first_escalation_budget.py tests/test_model_ops_cheap_first_cascade_research_gate.py tests/test_model_ops_readiness.py -q"
        if warning_category == "release_evidence_review":
            return "python -m pytest tests/test_model_ops_cheap_first_release_decision.py tests/test_model_ops_default_change_queue.py tests/test_model_ops_readiness.py -q"
        if warning_category == "configuration_review":
            return "python -m pytest tests/test_model_configuration_audit.py tests/test_model_gateway_connection_profile.py tests/test_model_gateway_runtime_configuration.py tests/test_model_gateway_compatibility.py tests/test_model_ops_readiness.py -q"
        if warning_category == "resilience_review":
            return "python -m pytest tests/test_model_routing_replay.py tests/test_model_fallback_chains.py tests/test_model_ops_readiness.py -q"
        return "python -m pytest tests/test_model_ops_readiness.py -q"


def _list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
