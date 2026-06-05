from __future__ import annotations

import re
from typing import Any

from services.model_capability_matrix import COST_RANK, ModelCapabilityMatrixService
from services.model_catalog import model_profile, task_default_model


SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|token)",
    re.IGNORECASE,
)

QUALITY_GATES: dict[str, tuple[str, ...]] = {
    "fast": ("json-schema-valid", "low-confidence-absent", "no-privacy-warning"),
    "ocr": ("ocr-text-present", "required-fields-present", "low-confidence-review"),
    "classification": ("required-label-present", "schema-valid", "confidence-threshold-met"),
    "review": ("risk-labels-present", "citation-check-passed", "human-review-ready"),
    "pdf": ("extraction-quality-pass", "page-count-known", "operator-review-recorded"),
    "grounded-research": ("source-citation-present", "source-recency-known", "rag-grounding-pass"),
    "agentic": ("plan-steps-bounded", "tool-risk-reviewed", "rollback-path-present"),
    "image": ("explicit-media-request", "rights-review-present", "client-delivery-blocked-by-default"),
}


class ModelRouteQualityBudgetService:
    """Review cheap-first route quality gates without running model calls."""

    def __init__(self, capability_matrix_service: ModelCapabilityMatrixService | None = None) -> None:
        self.capability_matrix_service = capability_matrix_service or ModelCapabilityMatrixService()

    def build_budget(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        matrix = self.capability_matrix_service.build_matrix()
        selected_tasks = self._selected_tasks(data.get("tasks"))
        matrix_rows = [
            row for row in matrix["tasks"] if not selected_tasks or row["task"] in selected_tasks
        ]
        rows = [self._task_budget_row(row) for row in matrix_rows]
        blocking_ids = self._blocking_ids(rows)
        warning_ids = self._warning_ids(rows)

        return {
            "status": "fail" if blocking_ids else ("warn" if warning_ids else "pass"),
            "method": {
                "type": "cheap-first-route-quality-budget",
                "notes": [
                    "Combines the capability matrix with deterministic quality gates before any gateway call.",
                    "Cheap models can start a task only when required capabilities and local quality gates are reviewable.",
                    "Premium or preview models remain explicit exceptions; this service returns metadata only.",
                ],
            },
            "summary": {
                "task_count": len(rows),
                "cheap_start_task_count": sum(1 for row in rows if row["cheap_start_model"] == "gemini-2.5-flash-lite"),
                "premium_exception_task_count": sum(1 for row in rows if row["premium_exception_allowed"]),
                "runtime_default_gap_count": sum(1 for row in rows if not row["runtime_default_has_required_capabilities"]),
                "quality_gate_count": sum(row["quality_gate_count"] for row in rows),
                "blocking_check_count": len(blocking_ids),
                "warning_check_count": len(warning_ids),
                "raw_payload_echoed": False,
            },
            "task_quality_budgets": rows,
            "checks": self._checks(rows, blocking_ids, warning_ids),
            "blocking_check_ids": blocking_ids,
            "warning_check_ids": warning_ids,
            "recommended_actions": self._recommended_actions(blocking_ids, warning_ids, rows),
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "task ids, model ids, cost tiers, capability booleans, quality gate ids, and review actions only",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_route_quality_budget.py tests/test_model_ops_readiness.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _task_budget_row(self, row: dict[str, Any]) -> dict[str, Any]:
        task = str(row.get("task") or "").strip()
        requirement = row.get("requirement") if isinstance(row.get("requirement"), dict) else {}
        required_capabilities = [str(item) for item in requirement.get("required_capabilities", [])]
        recommended_model = str(row.get("recommended_model") or "")
        runtime_default = str(row.get("runtime_default_model") or task_default_model(task))
        runtime_profile = model_profile(runtime_default)
        recommended_profile = model_profile(recommended_model)
        runtime_capabilities = set(runtime_profile.capabilities if runtime_profile else ())
        runtime_has_required = all(capability in runtime_capabilities for capability in required_capabilities)
        runtime_cost_tier = runtime_profile.cost_tier if runtime_profile else "unknown"
        max_cost_tier = str(requirement.get("max_cost_tier") or "unknown")
        default_over_budget = self._cost_rank(runtime_cost_tier) > self._cost_rank(max_cost_tier)
        quality_gates = list(QUALITY_GATES.get(task, ("schema-valid", "human-review-ready")))
        top_candidate = row.get("candidates", [{}])[0] if isinstance(row.get("candidates"), list) and row.get("candidates") else {}
        quality_score = int(top_candidate.get("fit_score") or 0)
        premium_exception_allowed = max_cost_tier == "premium" or runtime_cost_tier == "premium"

        return {
            "task": task,
            "display_name": str(requirement.get("display_name") or task),
            "recommended_model": recommended_model,
            "runtime_default_model": runtime_default,
            "cheap_start_model": "gemini-2.5-flash-lite" if task != "image" else recommended_model,
            "recommended_model_cost_tier": recommended_profile.cost_tier if recommended_profile else "unknown",
            "runtime_default_cost_tier": runtime_cost_tier,
            "max_cost_tier": max_cost_tier,
            "candidate_count": int(row.get("candidate_count") or 0),
            "quality_score": quality_score,
            "quality_floor": 75,
            "quality_gate_ids": quality_gates,
            "quality_gate_count": len(quality_gates),
            "runtime_default_has_required_capabilities": runtime_has_required,
            "runtime_default_over_budget": default_over_budget and not premium_exception_allowed,
            "premium_exception_allowed": premium_exception_allowed,
            "review_action": self._review_action(
                task,
                runtime_has_required=runtime_has_required,
                default_over_budget=default_over_budget and not premium_exception_allowed,
                candidate_count=int(row.get("candidate_count") or 0),
                quality_score=quality_score,
            ),
        }

    def _checks(self, rows: list[dict[str, Any]], blocking_ids: list[str], warning_ids: list[str]) -> list[dict[str, str]]:
        return [
            {
                "id": "candidate-present",
                "status": "fail" if "candidate-present" in blocking_ids else "pass",
                "reason": "Every task has at least one catalog candidate."
                if "candidate-present" not in blocking_ids
                else "At least one task has no catalog candidate.",
            },
            {
                "id": "quality-gates-present",
                "status": "fail" if "quality-gates-present" in blocking_ids else "pass",
                "reason": "Every task has deterministic quality gates before escalation."
                if "quality-gates-present" not in blocking_ids
                else "Add deterministic quality gates before allowing a route.",
            },
            {
                "id": "cheap-start-before-premium",
                "status": "pass",
                "reason": "Text tasks expose a cheap-start model before premium exception handling.",
            },
            {
                "id": "runtime-default-capability-review",
                "status": "warn" if "runtime-default-capability-review" in warning_ids else "pass",
                "reason": "Some runtime defaults need capability review before becoming cheap-first defaults."
                if "runtime-default-capability-review" in warning_ids
                else "Runtime defaults expose the required capabilities for their task budgets.",
            },
            {
                "id": "quality-score-floor-review",
                "status": "warn" if "quality-score-floor-review" in warning_ids else "pass",
                "reason": "Some route candidates have quality scores below the local review floor."
                if "quality-score-floor-review" in warning_ids
                else "Route candidate quality scores meet the local review floor.",
            },
        ]

    def _blocking_ids(self, rows: list[dict[str, Any]]) -> list[str]:
        blocking: list[str] = []
        if any(row["candidate_count"] <= 0 for row in rows):
            blocking.append("candidate-present")
        if any(row["quality_gate_count"] <= 0 for row in rows):
            blocking.append("quality-gates-present")
        return blocking

    def _warning_ids(self, rows: list[dict[str, Any]]) -> list[str]:
        warnings: list[str] = []
        if any(not row["runtime_default_has_required_capabilities"] for row in rows):
            warnings.append("runtime-default-capability-review")
        if any(row["runtime_default_over_budget"] for row in rows):
            warnings.append("runtime-default-budget-review")
        if any(row["quality_score"] < row["quality_floor"] for row in rows):
            warnings.append("quality-score-floor-review")
        return warnings

    def _recommended_actions(
        self,
        blocking_ids: list[str],
        warning_ids: list[str],
        rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking_ids:
            return [f"Resolve route quality blocker: {item}." for item in blocking_ids]
        actions = [f"Review route quality warning: {item}." for item in warning_ids]
        capability_gaps = [
            row["task"] for row in rows if not row["runtime_default_has_required_capabilities"]
        ]
        if capability_gaps:
            actions.append("Keep capability-gap tasks explicit-only until defaults are configured: " + ", ".join(capability_gaps) + ".")
        if not actions:
            actions.append("Keep cheap-first routes tied to deterministic quality gates before escalation.")
        return actions

    def _selected_tasks(self, value: Any) -> set[str]:
        if not isinstance(value, list):
            return set()
        tasks = {self._safe_token(item) for item in value[:20]}
        return {task for task in tasks if task}

    def _safe_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace("_", "-")[:80]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9:-]+", "-", raw).strip("-")

    def _cost_rank(self, tier: str) -> int:
        return COST_RANK.get(str(tier or "").strip().lower(), 99)

    def _review_action(
        self,
        task: str,
        *,
        runtime_has_required: bool,
        default_over_budget: bool,
        candidate_count: int,
        quality_score: int,
    ) -> str:
        if candidate_count <= 0:
            return "block_until_catalog_candidate_exists"
        if not runtime_has_required:
            return "configure_explicit_capable_default_before_release_claim"
        if default_over_budget:
            return "review_budget_before_default_use"
        if quality_score < 75:
            return "run_low_resource_fixture_before_escalation"
        if task in {"pdf", "image"}:
            return "explicit_exception_with_operator_review"
        return "cheap_first_with_quality_gate"
