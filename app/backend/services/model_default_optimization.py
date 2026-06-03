from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_catalog import estimate_token_cost_usd, model_profile
from services.model_cost_forecast import ModelCostForecastService


@dataclass(frozen=True)
class DefaultOptimizationTarget:
    task: str
    env_var: str | None
    source: str


DEFAULT_TARGETS: dict[str, DefaultOptimizationTarget] = {
    "fast": DefaultOptimizationTarget("fast", "APP_AI_FAST_MODEL", "configured_default"),
    "classification": DefaultOptimizationTarget("classification", "APP_AI_CLASSIFIER_MODEL", "configured_default"),
    "ocr": DefaultOptimizationTarget("ocr", "APP_OCR_MODEL", "configured_default"),
    "review": DefaultOptimizationTarget("review", "APP_AI_REVIEW_MODEL", "configured_default"),
    "pdf": DefaultOptimizationTarget("pdf", "APP_AI_PDF_MODEL", "configured_default"),
    "grounded-research": DefaultOptimizationTarget("grounded-research", None, "explicit_request_model"),
    "agentic": DefaultOptimizationTarget("agentic", None, "explicit_request_model"),
    "image": DefaultOptimizationTarget("image", None, "explicit_media_model"),
}


class ModelDefaultOptimizationService:
    """Build an operator-facing plan for keeping task defaults on cheap capable models."""

    def build_plan(
        self,
        capability_matrix: dict[str, Any] | None = None,
        cost_forecast: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        capability_matrix = capability_matrix or ModelCapabilityMatrixService().build_matrix()
        cost_forecast = cost_forecast or ModelCostForecastService().build_forecast()
        forecast_by_task = {
            str(row.get("task")): row
            for row in _list(cost_forecast.get("profiles"))
            if isinstance(row, dict)
        }
        rows = [
            self._recommendation(row, forecast_by_task.get(str(row.get("task"))))
            for row in _list(capability_matrix.get("tasks"))
            if isinstance(row, dict)
        ]
        status = self._status(rows)
        savings_rows = [row for row in rows if row["estimated_monthly_savings_usd"] is not None]
        total_savings = round(sum(float(row["estimated_monthly_savings_usd"] or 0.0) for row in savings_rows), 6)
        change_rows = [row for row in rows if row["requires_change"]]
        manual_rows = [row for row in rows if row["requires_operator_review"]]

        return {
            "status": status,
            "method": {
                "type": "default-model-optimization-plan",
                "notes": [
                    "Compares runtime defaults with the cheapest capable model from the capability matrix.",
                    "Uses forecast task volumes only for approximate savings; gateway billing may differ.",
                    "Does not read or return API keys, prompts, documents, file names, users, or raw model output.",
                ],
            },
            "summary": {
                "task_count": len(rows),
                "aligned_count": sum(1 for row in rows if row["status"] == "pass"),
                "change_count": len(change_rows),
                "manual_review_count": len(manual_rows),
                "estimated_monthly_savings_usd": total_savings,
                "priced_task_count": len(savings_rows),
            },
            "recommendations": rows,
            "blocking_check_ids": [row["id"] for row in rows if row["status"] == "fail"],
            "warning_check_ids": [row["id"] for row in rows if row["status"] == "warn"],
            "recommended_actions": self._recommended_actions(rows),
        }

    def _recommendation(self, row: dict[str, Any], forecast_row: dict[str, Any] | None) -> dict[str, Any]:
        task = str(row.get("task") or "unknown")
        requirement = row.get("requirement") if isinstance(row.get("requirement"), dict) else {}
        target = DEFAULT_TARGETS.get(task, DefaultOptimizationTarget(task, None, "explicit_request_model"))
        recommended_model = str(row.get("recommended_model") or "")
        current_model = str(row.get("runtime_default_model") or "")
        default_alias = str(requirement.get("default_alias") or "")
        configurable_default = target.env_var is not None and default_alias != "explicit"
        current_profile = model_profile(current_model)
        recommended_profile = model_profile(recommended_model)
        required_capabilities = [str(item) for item in _list(requirement.get("required_capabilities"))]
        missing_required = _missing_required(current_profile, required_capabilities)
        current_cost_tier = current_profile.cost_tier if current_profile else None
        recommended_cost_tier = recommended_profile.cost_tier if recommended_profile else None
        max_cost_tier = str(requirement.get("max_cost_tier") or "premium")
        over_budget = (
            _tier_rank(current_cost_tier) > _tier_rank(max_cost_tier)
            if current_cost_tier is not None
            else False
        )
        requires_change = configurable_default and current_model != recommended_model
        explicit_ready = not configurable_default and recommended_profile is not None
        status = self._row_status(
            configurable_default=configurable_default,
            explicit_ready=explicit_ready,
            requires_change=requires_change,
            current_profile=current_profile,
            recommended_profile=recommended_profile,
            missing_required=missing_required,
            over_budget=over_budget,
        )
        savings = self._estimated_savings_usd(current_model, recommended_model, forecast_row)
        requires_operator_review = recommended_cost_tier == "premium" or task in {"pdf", "image"}

        return {
            "id": f"default-optimization-{task}",
            "task": task,
            "display_name": str(requirement.get("display_name") or task),
            "status": status,
            "source": target.source,
            "env_var": target.env_var,
            "current_model": current_model,
            "recommended_model": recommended_model,
            "current_cost_tier": current_cost_tier,
            "recommended_cost_tier": recommended_cost_tier,
            "max_cost_tier": max_cost_tier,
            "required_capabilities": required_capabilities,
            "missing_required_capabilities": missing_required,
            "runtime_default_is_recommended": bool(row.get("runtime_default_is_recommended")),
            "requires_change": requires_change,
            "requires_operator_review": requires_operator_review,
            "estimated_monthly_savings_usd": savings,
            "reason": self._reason(
                task=task,
                configurable_default=configurable_default,
                requires_change=requires_change,
                explicit_ready=explicit_ready,
                missing_required=missing_required,
                over_budget=over_budget,
                recommended_model=recommended_model,
                env_var=target.env_var,
                savings=savings,
            ),
        }

    def _row_status(
        self,
        *,
        configurable_default: bool,
        explicit_ready: bool,
        requires_change: bool,
        current_profile: Any,
        recommended_profile: Any,
        missing_required: list[str],
        over_budget: bool,
    ) -> str:
        if recommended_profile is None:
            return "warn"
        if not configurable_default:
            return "pass" if explicit_ready else "warn"
        if current_profile is None:
            return "warn"
        if missing_required or over_budget:
            return "fail"
        if requires_change:
            return "warn"
        return "pass"

    def _estimated_savings_usd(
        self,
        current_model: str,
        recommended_model: str,
        forecast_row: dict[str, Any] | None,
    ) -> float | None:
        profile = forecast_row.get("profile") if isinstance(forecast_row, dict) else None
        if not isinstance(profile, dict):
            return None
        monthly_units = _int(profile.get("monthly_units"))
        prompt_tokens = _int(profile.get("prompt_tokens_per_unit"))
        completion_tokens = _int(profile.get("completion_tokens_per_unit"))
        current_cost = estimate_token_cost_usd(current_model, prompt_tokens, completion_tokens)
        recommended_cost = estimate_token_cost_usd(recommended_model, prompt_tokens, completion_tokens)
        if current_cost is None or recommended_cost is None:
            return None
        return round(max(0.0, (current_cost - recommended_cost) * monthly_units), 6)

    def _reason(
        self,
        *,
        task: str,
        configurable_default: bool,
        requires_change: bool,
        explicit_ready: bool,
        missing_required: list[str],
        over_budget: bool,
        recommended_model: str,
        env_var: str | None,
        savings: float | None,
    ) -> str:
        if not configurable_default:
            if explicit_ready:
                return f"Use {recommended_model} explicitly when enabling {task}; no default env var is changed."
            return f"Add a verified catalog entry before relying on the explicit {task} model."
        if missing_required:
            return f"Current default is missing required capabilities: {', '.join(missing_required)}."
        if over_budget:
            return "Current default exceeds this task's cost ceiling."
        if requires_change:
            if savings is not None and savings > 0:
                return f"Set {env_var} to {recommended_model} to restore the cheapest capable default and save about ${savings:.4f}/month."
            return f"Set {env_var} to {recommended_model} to align runtime default with the capability matrix."
        return f"{env_var} is aligned with the cheapest capable default for {task}."

    def _status(self, rows: list[dict[str, Any]]) -> str:
        if any(row["status"] == "fail" for row in rows):
            return "fail"
        if any(row["status"] == "warn" for row in rows):
            return "warn"
        return "pass"

    def _recommended_actions(self, rows: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        for row in rows:
            if row["status"] == "pass":
                continue
            if row["env_var"] and row["requires_change"]:
                actions.append(f"Set {row['env_var']}={row['recommended_model']} for {row['task']}.")
            elif row["missing_required_capabilities"]:
                actions.append(f"Choose a {row['task']} default with: {', '.join(row['missing_required_capabilities'])}.")
            else:
                actions.append(f"Review default optimization for {row['task']}.")
        if not actions:
            actions.append("Task defaults are aligned with the cheapest capable Gemini models.")
        return actions


def _missing_required(profile: Any, required_capabilities: list[str]) -> list[str]:
    if profile is None:
        return []
    capabilities = set(profile.capabilities)
    return sorted(set(required_capabilities) - capabilities)


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
