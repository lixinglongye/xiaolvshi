from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_catalog import estimate_token_cost_usd, model_profile, task_default_model
from services.model_request_policy import TASK_PARAMETER_POLICIES, resolve_generation_request_policy


@dataclass(frozen=True)
class RequestCostBound:
    task: str
    prompt_tokens: int
    warn_default_cost_usd: float
    fail_default_cost_usd: float
    warn_ceiling_cost_usd: float
    fail_ceiling_cost_usd: float


REQUEST_COST_BOUNDS: dict[str, RequestCostBound] = {
    "fast": RequestCostBound("fast", 1_200, 0.002, 0.005, 0.004, 0.01),
    "classification": RequestCostBound("classification", 1_600, 0.002, 0.005, 0.004, 0.01),
    "ocr": RequestCostBound("ocr", 1_800, 0.003, 0.008, 0.006, 0.015),
    "review": RequestCostBound("review", 22_000, 0.05, 0.12, 0.10, 0.25),
    "grounded-research": RequestCostBound("grounded-research", 18_000, 0.04, 0.10, 0.08, 0.18),
    "agentic": RequestCostBound("agentic", 8_000, 0.02, 0.05, 0.04, 0.10),
    "pdf": RequestCostBound("pdf", 110_000, 0.40, 0.90, 0.60, 1.20),
}


class ModelRequestCostBoundsService:
    """Estimate per-request cost ceilings from task defaults and max token policy."""

    def evaluate(self) -> dict[str, Any]:
        rows = [self._row(bound) for bound in REQUEST_COST_BOUNDS.values()]
        status = self._status(rows)
        blocking = [row for row in rows if row["status"] == "fail"]
        warnings = [row for row in rows if row["status"] == "warn"]
        return {
            "status": status,
            "method": {
                "type": "request-cost-bounds",
                "notes": [
                    "Estimates default and ceiling request cost from task max_tokens policy and catalog pricing.",
                    "Prompt token assumptions mirror the monthly cost forecast profile sizes.",
                    "Does not read prompts, documents, file names, users, emails, API keys, or raw model output.",
                ],
            },
            "summary": {
                "task_count": len(rows),
                "priced_task_count": sum(1 for row in rows if row["is_priced"]),
                "default_cost_usd": round(sum(row["default_request_cost_usd"] or 0.0 for row in rows), 6),
                "ceiling_cost_usd": round(sum(row["ceiling_request_cost_usd"] or 0.0 for row in rows), 6),
                "warning_count": len(warnings),
                "blocking_count": len(blocking),
            },
            "task_bounds": rows,
            "blocking_check_ids": [row["id"] for row in blocking],
            "warning_check_ids": [row["id"] for row in warnings],
            "recommended_actions": self._recommended_actions(rows),
        }

    def _row(self, bound: RequestCostBound) -> dict[str, Any]:
        policy = TASK_PARAMETER_POLICIES[bound.task]
        decision = resolve_generation_request_policy(task=bound.task)
        model = task_default_model(bound.task)
        profile = model_profile(model)
        default_cost = estimate_token_cost_usd(model, bound.prompt_tokens, decision.effective_max_tokens)
        ceiling_cost = estimate_token_cost_usd(model, bound.prompt_tokens, policy.max_max_tokens)
        status = self._row_status(bound, profile, default_cost, ceiling_cost)
        return {
            "id": f"request-cost-bound-{bound.task}",
            "task": bound.task,
            "model": model,
            "is_priced": default_cost is not None and ceiling_cost is not None,
            "cost_tier": profile.cost_tier if profile else None,
            "prompt_tokens_assumption": bound.prompt_tokens,
            "default_max_tokens": decision.effective_max_tokens,
            "ceiling_max_tokens": policy.max_max_tokens,
            "default_request_cost_usd": default_cost,
            "ceiling_request_cost_usd": ceiling_cost,
            "warn_default_cost_usd": bound.warn_default_cost_usd,
            "fail_default_cost_usd": bound.fail_default_cost_usd,
            "warn_ceiling_cost_usd": bound.warn_ceiling_cost_usd,
            "fail_ceiling_cost_usd": bound.fail_ceiling_cost_usd,
            "status": status,
            "reason": self._reason(bound, profile, default_cost, ceiling_cost, status),
        }

    def _row_status(
        self,
        bound: RequestCostBound,
        profile: Any,
        default_cost: float | None,
        ceiling_cost: float | None,
    ) -> str:
        if profile is None or default_cost is None or ceiling_cost is None:
            return "warn"
        if default_cost >= bound.fail_default_cost_usd or ceiling_cost >= bound.fail_ceiling_cost_usd:
            return "fail"
        if default_cost >= bound.warn_default_cost_usd or ceiling_cost >= bound.warn_ceiling_cost_usd:
            return "warn"
        if bound.task in {"fast", "classification", "ocr"} and COST_TIER_RANK.get(profile.cost_tier, 99) > COST_TIER_RANK["lowest"]:
            return "fail"
        if bound.task in {"grounded-research", "agentic"} and COST_TIER_RANK.get(profile.cost_tier, 99) > COST_TIER_RANK["low"]:
            return "fail"
        return "pass"

    def _reason(
        self,
        bound: RequestCostBound,
        profile: Any,
        default_cost: float | None,
        ceiling_cost: float | None,
        status: str,
    ) -> str:
        if profile is None or default_cost is None or ceiling_cost is None:
            return "Model pricing is unknown; add catalog pricing before relying on request cost bounds."
        if status == "fail":
            return "Default or ceiling request cost exceeds the fail threshold for this task."
        if status == "warn":
            return "Request cost is within the hard limit but needs maintainer review before increasing volume."
        return f"{bound.task} request cost stays within cheap-first bounds."

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
            if not row["is_priced"]:
                actions.append(f"Add pricing metadata for {row['model']} before using it for {row['task']}.")
            else:
                actions.append(f"Lower {row['task']} max_tokens or move the task back to a cheaper Gemini model.")
        if not actions:
            actions.append("Per-request model cost bounds are within policy for all tracked tasks.")
        return actions
