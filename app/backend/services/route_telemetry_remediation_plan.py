from __future__ import annotations

from typing import Any

from services.model_default_optimization import ModelDefaultOptimizationService
from services.route_telemetry_triage_queue import RouteTelemetryTriageQueueService


TRIAGE_TO_TARGETS: dict[str, tuple[str, ...]] = {
    "failure-rate": ("review", "pdf"),
    "over-budget-ratio": ("fast", "classification", "ocr", "review"),
    "operator-review-ratio": ("review", "pdf"),
    "premium-request-ratio": ("fast", "classification", "ocr", "review", "pdf"),
    "unknown-model-count": ("fast", "classification", "ocr", "review", "pdf"),
    "daily-route-hotspot": ("fast", "classification", "ocr", "review"),
    "collect-staging-events": ("fast", "classification", "ocr", "review"),
}


class RouteTelemetryRemediationPlanService:
    """Create concrete remediation steps from route telemetry triage evidence."""

    def __init__(
        self,
        triage_service: RouteTelemetryTriageQueueService | None = None,
        default_optimization_service: ModelDefaultOptimizationService | None = None,
    ) -> None:
        self.triage_service = triage_service or RouteTelemetryTriageQueueService()
        self.default_optimization_service = default_optimization_service or ModelDefaultOptimizationService()

    def build_plan(
        self,
        triage_payload: dict[str, Any] | None = None,
        default_optimization: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        triage = triage_payload if isinstance(triage_payload, dict) else self.triage_service.build_queue()
        optimization = (
            default_optimization if isinstance(default_optimization, dict) else self.default_optimization_service.build_plan()
        )
        optimization_rows = {
            str(row.get("task")): row
            for row in _list(optimization.get("recommendations"))
            if isinstance(row, dict)
        }
        steps = self._steps(triage, optimization_rows)
        blocking = [step for step in steps if step["severity"] == "fail"]
        warnings = [step for step in steps if step["severity"] == "warn"]
        env_changes = [step for step in steps if step["env_var"] and step["requires_env_change"]]
        status = self._status(blocking, warnings, triage)

        return {
            "status": status,
            "method": {
                "type": "route-telemetry-remediation-plan",
                "notes": [
                    "Consumes route telemetry triage and default optimization metadata only.",
                    "Produces operator-reviewed .env and validation suggestions; it never writes configuration.",
                    "Does not call NewAPI, Gemini, OpenAI, or any gateway.",
                    "Does not read prompts, legal text, request bodies, response bodies, credentials, emails, or raw model outputs.",
                ],
            },
            "summary": {
                "remediation_step_count": len(steps),
                "blocking_step_count": len(blocking),
                "warning_step_count": len(warnings),
                "env_change_count": len(env_changes),
                "manual_review_step_count": sum(1 for step in steps if step["requires_operator_review"]),
                "source_triage_status": str(triage.get("status") or "missing"),
                "source_triage_item_count": _int(_dict(triage.get("summary")).get("triage_item_count")),
                "default_optimization_status": str(optimization.get("status") or "missing"),
                "estimated_monthly_savings_usd": round(
                    sum(_float(step.get("estimated_monthly_savings_usd")) for step in steps),
                    6,
                ),
                "newapi_called": False,
                "configuration_written": False,
            },
            "remediation_steps": steps,
            "blocking_step_ids": [step["id"] for step in blocking],
            "warning_step_ids": [step["id"] for step in warnings],
            "recommended_env": self._recommended_env(steps),
            "recommended_actions": self._recommended_actions(status, steps),
            "release_guardrails": [
                "Apply .env changes manually and review diffs before restarting model traffic.",
                "Do not promote premium or unknown models as defaults from telemetry alone.",
                "Run the listed low-resource tests before using telemetry as release evidence.",
                "Keep prompts, legal text, gateway payloads, credentials, emails, and model outputs out of remediation records.",
            ],
            "privacy_boundary": {
                "source": "route_telemetry_triage + default_optimization",
                "raw_payload_storage_allowed": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "credentials_included": False,
                "raw_model_output_included": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_remediation_plan.py -q",
                "python -m pytest tests/test_route_telemetry_triage_queue.py tests/test_model_default_optimization.py -q",
            ],
        }

    def _steps(self, triage: dict[str, Any], optimization_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        items = [item for item in _list(triage.get("triage_items")) if isinstance(item, dict)]
        triage_summary = _dict(triage.get("summary"))
        actionable_items = [item for item in items if str(item.get("severity")) in {"fail", "warn"}]
        if not items or (_bool(triage_summary.get("empty_repository")) and not actionable_items):
            return [self._no_action_step(triage)]

        steps: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in actionable_items:
            check_id = str(item.get("check_id") or "unknown")
            for task in TRIAGE_TO_TARGETS.get(check_id, ("fast", "review")):
                row = optimization_rows.get(task)
                step = self._step_from_triage(item, task, row)
                if step["id"] in seen:
                    continue
                seen.add(step["id"])
                steps.append(step)
        return sorted(steps, key=lambda step: (-_int(step.get("priority")), str(step.get("id"))))

    def _step_from_triage(
        self,
        item: dict[str, Any],
        task: str,
        optimization_row: dict[str, Any] | None,
    ) -> dict[str, Any]:
        severity = self._step_severity(str(item.get("severity") or "info"), optimization_row)
        env_var = str((optimization_row or {}).get("env_var") or "")
        current_model = str((optimization_row or {}).get("current_model") or "")
        recommended_model = str((optimization_row or {}).get("recommended_model") or "")
        requires_change = bool((optimization_row or {}).get("requires_change"))
        operator_review = bool((optimization_row or {}).get("requires_operator_review")) or severity == "fail"
        env_assignment = f"{env_var}={recommended_model}" if env_var and recommended_model else None

        return {
            "id": f"remediate-{item.get('check_id', 'unknown')}-{task}",
            "title": f"Remediate {task} routing for {item.get('check_id', 'route telemetry')}",
            "severity": severity,
            "priority": _int(item.get("priority")) + self._task_priority(task),
            "source_triage_item_id": str(item.get("id") or ""),
            "source_check_id": str(item.get("check_id") or "unknown"),
            "task": task,
            "env_var": env_var or None,
            "current_model": current_model or None,
            "recommended_model": recommended_model or None,
            "recommended_env_assignment": env_assignment,
            "requires_env_change": bool(env_assignment and requires_change),
            "requires_operator_review": operator_review,
            "estimated_monthly_savings_usd": (optimization_row or {}).get("estimated_monthly_savings_usd"),
            "reason": self._reason(item, task, optimization_row),
            "action": self._action(item, task, optimization_row),
            "validation_commands": self._validation_commands(task),
            "release_gate_links": [
                "route-telemetry-remediation-plan",
                "route-telemetry-triage-queue",
                "route-telemetry-ops-summary",
                "model-default-optimization",
            ],
            "evidence_paths": [
                "app/backend/services/route_telemetry_remediation_plan.py",
                "app/backend/services/route_telemetry_triage_queue.py",
                "app/backend/services/model_default_optimization.py",
            ],
        }

    def _no_action_step(self, triage: dict[str, Any]) -> dict[str, Any]:
        status = str(triage.get("status") or "missing")
        return {
            "id": "remediate-route-telemetry-no-action",
            "title": "Keep cheap-first route defaults",
            "severity": "info",
            "priority": 20,
            "source_triage_item_id": "",
            "source_check_id": "no-triage-actions",
            "task": "model_ops",
            "env_var": None,
            "current_model": None,
            "recommended_model": None,
            "recommended_env_assignment": None,
            "requires_env_change": False,
            "requires_operator_review": status == "ready",
            "estimated_monthly_savings_usd": None,
            "reason": "No blocking or warning telemetry triage actions were found.",
            "action": (
                "Collect sanitized staging route events before claiming production routing health."
                if status == "ready"
                else "Keep current cheap-first defaults and continue low-resource validation."
            ),
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_remediation_plan.py -q",
            ],
            "release_gate_links": [
                "route-telemetry-remediation-plan",
                "route-telemetry-triage-queue",
            ],
            "evidence_paths": [
                "app/backend/services/route_telemetry_remediation_plan.py",
                "docs/ROUTE_TELEMETRY_REMEDIATION_PLAN.md",
            ],
        }

    def _step_severity(self, triage_severity: str, optimization_row: dict[str, Any] | None) -> str:
        if triage_severity == "fail":
            return "fail"
        row_status = str((optimization_row or {}).get("status") or "pass")
        if row_status == "fail":
            return "fail"
        if triage_severity == "warn" or row_status == "warn":
            return "warn"
        return "info"

    def _task_priority(self, task: str) -> int:
        return {
            "fast": 8,
            "classification": 7,
            "ocr": 6,
            "review": 5,
            "pdf": 3,
        }.get(task, 0)

    def _reason(self, item: dict[str, Any], task: str, optimization_row: dict[str, Any] | None) -> str:
        triage_reason = f"Route telemetry triage: {item.get('reason') or 'triage item needs review.'}"
        if not optimization_row:
            return f"{triage_reason} No default optimization row exists for {task}."
        return f"{triage_reason} Default optimization says: {optimization_row.get('reason')}"

    def _action(self, item: dict[str, Any], task: str, optimization_row: dict[str, Any] | None) -> str:
        env_var = str((optimization_row or {}).get("env_var") or "")
        recommended = str((optimization_row or {}).get("recommended_model") or "")
        requires_change = bool((optimization_row or {}).get("requires_change"))
        if env_var and recommended and requires_change:
            return f"Review and apply {env_var}={recommended} to restore cheap-first routing, then rerun route telemetry and model-ops readiness checks."
        if env_var and recommended:
            return f"Keep {env_var} on cheap-first model {recommended}; investigate telemetry source before escalating {task} defaults."
        if str(item.get("check_id")) == "unknown-model-count":
            return "Catalog unknown Gemini-like gateway model pricing, lifecycle, and capabilities before routing defaults depend on it."
        return f"Review {task} route behavior and keep cheap-first defaults unless fixture evidence requires escalation."

    def _validation_commands(self, task: str) -> list[str]:
        commands = [
            "python -m pytest tests/test_route_telemetry_remediation_plan.py -q",
            "python -m pytest tests/test_route_telemetry_triage_queue.py tests/test_route_telemetry_ops_summary.py -q",
        ]
        if task in {"fast", "classification", "ocr", "review", "pdf"}:
            commands.append("python -m pytest tests/test_model_default_optimization.py tests/test_model_runtime_router.py -q")
        return commands

    def _recommended_env(self, steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for step in steps:
            env_var = step.get("env_var")
            recommended = step.get("recommended_model")
            if not env_var or not recommended or str(env_var) in seen:
                continue
            seen.add(str(env_var))
            rows.append(
                {
                    "env_var": env_var,
                    "task": step["task"],
                    "current_value": step.get("current_model"),
                    "recommended_value": recommended,
                    "requires_change": bool(step.get("requires_env_change")),
                    "source_step_id": step["id"],
                    "reason": step["reason"],
                }
            )
        return rows

    def _recommended_actions(self, status: str, steps: list[dict[str, Any]]) -> list[str]:
        actionable = [step for step in steps if step["severity"] in {"fail", "warn"}]
        if actionable:
            return [str(step["action"]) for step in actionable[:4]]
        if status == "ready":
            return ["Collect sanitized staging route events before using remediation evidence as production health proof."]
        return ["No remediation steps are blocking cheap-first Gemini/NewAPI routing."]

    def _status(self, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]], triage: dict[str, Any]) -> str:
        if blocking:
            return "fail"
        if warnings:
            return "warn"
        return "ready" if str(triage.get("status")) == "ready" else "pass"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _float(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _bool(value: Any) -> bool:
    return bool(value)
