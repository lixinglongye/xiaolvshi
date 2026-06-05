from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_catalog import estimate_token_cost_usd, model_profile, task_default_model
from services.model_cost_forecast import ModelCostForecastService
from services.model_ops_gemini_default_change_review import TASK_ENV_VARS


HIGH_VOLUME_TASKS = {"fast", "ocr", "classification", "agentic", "grounded-research"}
STRICT_HIGH_VOLUME_COST_REGRESSION_TASKS = {"fast", "ocr", "classification"}
PREMIUM_EXCEPTION_TASKS = {"pdf", "image"}


@dataclass(frozen=True)
class ImpactProfile:
    task: str
    display_name: str
    monthly_units: int
    prompt_tokens_per_unit: int
    completion_tokens_per_unit: int
    max_cost_tier: str
    rationale: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


EXTRA_IMPACT_PROFILES: tuple[ImpactProfile, ...] = (
    ImpactProfile(
        task="agentic",
        display_name="Agentic planning and tool-routing",
        monthly_units=1_200,
        prompt_tokens_per_unit=3_500,
        completion_tokens_per_unit=800,
        max_cost_tier="low",
        rationale="Agentic planning can fan out into multiple calls, so default changes need cost-regression review.",
    ),
    ImpactProfile(
        task="grounded-research",
        display_name="Grounded legal research",
        monthly_units=700,
        prompt_tokens_per_unit=8_000,
        completion_tokens_per_unit=2_200,
        max_cost_tier="low",
        rationale="Grounded research is source-heavy and should stay cheap-first unless a premium exception is reviewed.",
    ),
    ImpactProfile(
        task="image",
        display_name="Image generation and editing",
        monthly_units=120,
        prompt_tokens_per_unit=600,
        completion_tokens_per_unit=0,
        max_cost_tier="premium",
        rationale="Media routes use separate pricing and should remain explicit premium/media exceptions.",
    ),
)


class ModelOpsGeminiDefaultCostImpactService:
    """Estimate cost impact for proposed Gemini defaults without changing them."""

    def __init__(self, forecast_service: ModelCostForecastService | None = None) -> None:
        self.forecast_service = forecast_service or ModelCostForecastService()

    def build_impact(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        profiles = self._impact_profiles()
        proposals = self._proposed_changes(payload)
        rows = [self._impact_row(proposal, profiles) for proposal in proposals]
        blocked = [row for row in rows if row["impact_status"] == "blocked"]
        review = [row for row in rows if row["impact_status"] == "review_required"]
        ready = [row for row in rows if row["impact_status"] == "ready"]
        priced_rows = [row for row in rows if row["current_monthly_cost_usd"] is not None and row["proposed_monthly_cost_usd"] is not None]
        monthly_delta = round(sum(float(row["monthly_delta_usd"] or 0.0) for row in priced_rows), 6)

        return {
            "status": "blocked" if blocked else ("review_required" if review else "ready"),
            "method": {
                "type": "model-ops-gemini-default-cost-impact",
                "notes": [
                    "Estimates monthly cost deltas for proposed Gemini default model changes using local task profiles.",
                    "Uses checked-in model catalog prices and forecast assumptions only; gateway billing may differ.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network and never writes configuration.",
                ],
            },
            "summary": {
                "proposal_count": len(rows),
                "priced_proposal_count": len(priced_rows),
                "ready_count": len(ready),
                "review_required_count": len(review),
                "blocked_count": len(blocked),
                "cost_increase_count": sum(1 for row in priced_rows if float(row["monthly_delta_usd"] or 0) > 0),
                "cost_decrease_count": sum(1 for row in priced_rows if float(row["monthly_delta_usd"] or 0) < 0),
                "unknown_price_count": len(rows) - len(priced_rows),
                "premium_exception_count": sum(1 for row in rows if row["premium_exception"]),
                "estimated_monthly_delta_usd": monthly_delta,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
            },
            "impact_rows": rows,
            "blocking_impact_ids": [row["id"] for row in blocked],
            "review_impact_ids": [row["id"] for row in review],
            "recommended_actions": self._recommended_actions(blocked, review, ready, monthly_delta),
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "real_env_read": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "model_outputs_included": False,
                "output_scope": "task ids, env var names, model ids, local cost metadata, forecast assumptions, status labels, and validation commands",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "billing_accuracy_claimed": False,
                "production_savings_claimed": False,
                "public_benchmark_scores_included": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_default_cost_impact.py tests/test_model_cost_forecast.py -q",
                "python -m pytest tests/test_model_ops_gemini_default_change_review.py tests/test_model_ops_readiness.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _impact_profiles(self) -> dict[str, ImpactProfile]:
        profiles: dict[str, ImpactProfile] = {}
        forecast = self.forecast_service.build_forecast()
        for row in forecast.get("profiles", []):
            if not isinstance(row, dict):
                continue
            profile = row.get("profile")
            if not isinstance(profile, dict):
                continue
            task = str(profile.get("task") or row.get("task") or "").strip()
            if not task:
                continue
            profiles[task] = ImpactProfile(
                task=task,
                display_name=str(profile.get("display_name") or task),
                monthly_units=_int(profile.get("monthly_units")),
                prompt_tokens_per_unit=_int(profile.get("prompt_tokens_per_unit")),
                completion_tokens_per_unit=_int(profile.get("completion_tokens_per_unit")),
                max_cost_tier="premium" if task in PREMIUM_EXCEPTION_TASKS else ("low" if task == "review" else "lowest"),
                rationale=str(profile.get("rationale") or row.get("recommended_action") or ""),
            )
        for profile in EXTRA_IMPACT_PROFILES:
            profiles.setdefault(profile.task, profile)
        return profiles

    def _proposed_changes(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw = payload.get("proposed_changes")
        if isinstance(raw, list) and raw:
            return [item for item in raw[:20] if isinstance(item, dict)]
        return [
            {
                "task": "agentic",
                "env_var": TASK_ENV_VARS["agentic"],
                "current_model": task_default_model("agentic"),
                "proposed_model": task_default_model("agentic"),
            },
            {
                "task": "grounded-research",
                "env_var": TASK_ENV_VARS["grounded-research"],
                "current_model": task_default_model("grounded-research"),
                "proposed_model": "gemini-3.1-pro-preview",
            },
        ]

    def _impact_row(self, proposal: dict[str, Any], profiles: dict[str, ImpactProfile]) -> dict[str, Any]:
        task = _normalize_task(str(proposal.get("task") or "fast"))
        profile = profiles.get(task) or self._fallback_profile(task)
        env_var = str(proposal.get("env_var") or TASK_ENV_VARS.get(task, "APP_AI_MODEL"))
        current_model = str(proposal.get("current_model") or task_default_model(task))
        proposed_model = str(proposal.get("proposed_model") or current_model)
        current_unit_cost = self._unit_cost(current_model, profile)
        proposed_unit_cost = self._unit_cost(proposed_model, profile)
        current_monthly = _monthly_cost(current_unit_cost, profile.monthly_units)
        proposed_monthly = _monthly_cost(proposed_unit_cost, profile.monthly_units)
        monthly_delta = _cost_delta(proposed_monthly, current_monthly)
        current_profile = model_profile(current_model)
        proposed_profile = model_profile(proposed_model)
        current_tier = current_profile.cost_tier if current_profile else "unknown"
        proposed_tier = proposed_profile.cost_tier if proposed_profile else "unknown"
        premium_exception = task in PREMIUM_EXCEPTION_TASKS or _tier_rank(proposed_tier) > _tier_rank(profile.max_cost_tier)
        cost_regression = monthly_delta is not None and monthly_delta > 0
        reason_codes = self._reason_codes(
            task=task,
            proposed_profile=proposed_profile,
            proposed_tier=proposed_tier,
            max_cost_tier=profile.max_cost_tier,
            current_unit_cost=current_unit_cost,
            proposed_unit_cost=proposed_unit_cost,
            monthly_delta=monthly_delta,
            premium_exception=premium_exception,
        )
        impact_status = self._impact_status(reason_codes)

        return {
            "id": f"gemini-default-cost-impact-{task}",
            "task": task,
            "env_var": env_var,
            "current_model": current_model,
            "proposed_model": proposed_model,
            "profile": profile.to_api(),
            "current_cost_tier": current_tier,
            "proposed_cost_tier": proposed_tier,
            "current_unit_cost_usd": current_unit_cost,
            "proposed_unit_cost_usd": proposed_unit_cost,
            "current_monthly_cost_usd": current_monthly,
            "proposed_monthly_cost_usd": proposed_monthly,
            "monthly_delta_usd": monthly_delta,
            "estimated_savings_delta_usd": None if monthly_delta is None else round(-monthly_delta, 6),
            "cost_regression": cost_regression,
            "premium_exception": premium_exception,
            "impact_status": impact_status,
            "release_action": self._release_action(impact_status),
            "reason_codes": reason_codes,
        }

    def _unit_cost(self, model: str, profile: ImpactProfile) -> float | None:
        model_meta = model_profile(model)
        if model_meta and model_meta.output_usd_per_image is not None:
            return round(model_meta.output_usd_per_image, 8)
        return estimate_token_cost_usd(
            model,
            profile.prompt_tokens_per_unit,
            profile.completion_tokens_per_unit,
        )

    def _fallback_profile(self, task: str) -> ImpactProfile:
        return ImpactProfile(
            task=task,
            display_name=task,
            monthly_units=100,
            prompt_tokens_per_unit=2_000,
            completion_tokens_per_unit=500,
            max_cost_tier="premium" if task in PREMIUM_EXCEPTION_TASKS else "low",
            rationale="Fallback metadata profile for explicit model default impact review.",
        )

    def _reason_codes(
        self,
        *,
        task: str,
        proposed_profile: Any,
        proposed_tier: str,
        max_cost_tier: str,
        current_unit_cost: float | None,
        proposed_unit_cost: float | None,
        monthly_delta: float | None,
        premium_exception: bool,
    ) -> list[str]:
        codes: list[str] = []
        if proposed_profile is None:
            codes.append("proposed-price-metadata-missing")
        elif proposed_profile.status != "stable":
            codes.append(f"lifecycle-{proposed_profile.status}")
        if current_unit_cost is None:
            codes.append("current-price-metadata-missing")
        if proposed_unit_cost is None:
            codes.append("proposed-price-metadata-missing")
        if _tier_rank(proposed_tier) > _tier_rank(max_cost_tier):
            codes.append("over-task-cost-budget")
        if monthly_delta is not None and monthly_delta > 0:
            codes.append("monthly-cost-increase")
            if task in STRICT_HIGH_VOLUME_COST_REGRESSION_TASKS:
                codes.append("high-volume-cheap-first-regression")
            elif task in HIGH_VOLUME_TASKS and not premium_exception:
                codes.append("cheap-first-cost-regression")
        if premium_exception:
            codes.append("manual-premium-exception-review")
        return _dedupe(codes) or ["cost-impact-ready"]

    def _impact_status(self, reason_codes: list[str]) -> str:
        blocking = {
            "proposed-price-metadata-missing",
            "high-volume-cheap-first-regression",
            "cheap-first-cost-regression",
        }
        if any(code in blocking for code in reason_codes):
            return "blocked"
        if any(code != "cost-impact-ready" for code in reason_codes):
            return "review_required"
        return "ready"

    def _release_action(self, impact_status: str) -> str:
        if impact_status == "ready":
            return "eligible_for_default_change_review"
        if impact_status == "blocked":
            return "block_default_change_until_cost_review"
        return "require_maintainer_cost_review"

    def _recommended_actions(
        self,
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        ready: list[dict[str, Any]],
        monthly_delta: float,
    ) -> list[str]:
        if blocked:
            return [
                "Do not promote blocked default changes until missing pricing or cheap-first cost regressions are resolved.",
                "Keep high-volume tasks on low-cost Gemini defaults unless separate benchmark and maintainer evidence justifies escalation.",
            ]
        if review:
            return [
                "Review premium exceptions, preview lifecycle, and positive monthly deltas before editing defaults.",
                f"Estimated combined monthly delta is ${monthly_delta:.6f}; confirm gateway billing separately before applying changes.",
            ]
        if ready:
            return ["Cost impact is ready for default-change review; rerun after any catalog or pricing metadata change."]
        return ["Submit sanitized default-change proposals before editing Gemini defaults."]


def _normalize_task(task: str) -> str:
    value = (task or "fast").strip().lower().replace("_", "-")
    aliases = {
        "classifier": "classification",
        "legal-review": "review",
        "chat": "review",
        "workflow-planning": "agentic",
        "rag-research": "grounded-research",
        "research": "grounded-research",
        "genimg": "image",
        "visual": "image",
    }
    return aliases.get(value, value)


def _monthly_cost(unit_cost: float | None, monthly_units: int) -> float | None:
    if unit_cost is None:
        return None
    return round(unit_cost * max(0, monthly_units), 6)


def _cost_delta(proposed: float | None, current: float | None) -> float | None:
    if proposed is None or current is None:
        return None
    return round(proposed - current, 6)


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
