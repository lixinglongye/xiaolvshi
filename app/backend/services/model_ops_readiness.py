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
    ReadinessComponent("default-optimization", "Default optimization plan", "configuration", "default_optimization"),
    ReadinessComponent("gateway-compatibility", "Gateway compatibility", "configuration", "gateway_compatibility"),
    ReadinessComponent("gateway-health-plan", "Gateway health plan", "configuration", "gateway_health_plan"),
    ReadinessComponent("gemini-variant-matrix", "Gemini variant matrix", "configuration", "gemini_variant_matrix"),
    ReadinessComponent("catalog-source-audit", "Gemini catalog source audit", "configuration", "catalog_source_audit"),
    ReadinessComponent(
        "gateway-probe-evaluation",
        "Gateway probe evaluation",
        "manual_evidence",
        "gateway_probe_evaluation",
        required=False,
    ),
    ReadinessComponent("lifecycle-policy", "Gemini lifecycle policy", "configuration", "lifecycle_policy"),
    ReadinessComponent("budget-policy", "Budget policy", "routing", "budget_policy"),
    ReadinessComponent("capability-matrix", "Capability matrix", "routing", "capability_matrix"),
    ReadinessComponent("runtime-router", "Runtime router", "routing", "runtime_router"),
    ReadinessComponent("reasoning-policy", "Reasoning policy", "routing", "reasoning_policy"),
    ReadinessComponent("request-policy", "Request policy", "routing", "request_policy"),
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
        "model-ops-performance-budget",
        "ModelOps performance budget",
        "runtime_evidence",
        "model_ops_performance_budget",
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
            },
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
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
        if value in {"advance_next_batch", "approval_ready", "drill_ready", "manifest_ready", "monitor_only"}:
            return "pass"
        if value in {
            "warn",
            "warning",
            "manual_review",
            "review_required",
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


def _list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
