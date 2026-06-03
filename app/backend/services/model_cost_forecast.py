from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_catalog import estimate_token_cost_usd, premium_text_model, resolve_model, task_default_model
from services.model_escalation_policy import ModelEscalationPolicyService


@dataclass(frozen=True)
class ForecastProfile:
    task: str
    display_name: str
    monthly_units: int
    prompt_tokens_per_unit: int
    completion_tokens_per_unit: int
    expected_escalation_rate: float
    baseline_model_alias: str
    rationale: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class ModelCostForecastService:
    """Forecast monthly model cost for cheap-first routing compared with premium-only routing."""

    def build_forecast(self) -> dict[str, Any]:
        rows = [self._forecast_row(profile) for profile in self._profiles()]
        priced_rows = [row for row in rows if row["cheap_first_monthly_cost_usd"] is not None]
        total_cheap = round(sum(row["cheap_first_monthly_cost_usd"] or 0 for row in rows), 6)
        total_baseline = round(sum(row["premium_baseline_monthly_cost_usd"] or 0 for row in rows), 6)
        total_savings = _savings_ratio(total_cheap, total_baseline)

        return {
            "status": "ready",
            "method": {
                "unit": "monthly forecast based on configurable task profiles",
                "source_basis": [
                    "Gemini paid-tier token prices from the local model catalog and Google Gemini pricing documentation.",
                    "Cheap-first cascade rationale follows FrugalGPT-style cost-quality routing.",
                ],
                "limitations": [
                    "Forecasts are planning estimates; gateway billing, cache discounts, batch pricing, and long-context breakpoints may differ.",
                    "Default volumes are maintenance assumptions, not production analytics.",
                    "The forecast never stores prompts, documents, API keys, or user identifiers.",
                ],
            },
            "summary": {
                "profile_count": len(rows),
                "priced_profile_count": len(priced_rows),
                "cheap_first_monthly_cost_usd": total_cheap,
                "premium_baseline_monthly_cost_usd": total_baseline,
                "estimated_savings_ratio": total_savings,
                "estimated_savings_usd": round(max(0.0, total_baseline - total_cheap), 6),
            },
            "profiles": rows,
        }

    def _profiles(self) -> tuple[ForecastProfile, ...]:
        return (
            ForecastProfile(
                task="fast",
                display_name="Preflight, routing, and light extraction",
                monthly_units=5_000,
                prompt_tokens_per_unit=1_200,
                completion_tokens_per_unit=180,
                expected_escalation_rate=0.04,
                baseline_model_alias="auto-pdf",
                rationale="High-volume low-risk tasks should stay on Flash-Lite unless confidence or schema checks fail.",
            ),
            ForecastProfile(
                task="classification",
                display_name="Material classification",
                monthly_units=2_500,
                prompt_tokens_per_unit=1_600,
                completion_tokens_per_unit=220,
                expected_escalation_rate=0.06,
                baseline_model_alias="auto-pdf",
                rationale="Classification can usually be handled by cheap JSON-capable models after deterministic rules.",
            ),
            ForecastProfile(
                task="ocr",
                display_name="OCR and extraction assist",
                monthly_units=3_500,
                prompt_tokens_per_unit=1_800,
                completion_tokens_per_unit=260,
                expected_escalation_rate=0.08,
                baseline_model_alias="auto-pdf",
                rationale="OCR runs per page or chunk, so failed extraction pages are escalated selectively.",
            ),
            ForecastProfile(
                task="review",
                display_name="Balanced legal review",
                monthly_units=450,
                prompt_tokens_per_unit=22_000,
                completion_tokens_per_unit=5_500,
                expected_escalation_rate=0.12,
                baseline_model_alias="auto-pdf",
                rationale="Routine reviews start on Flash and escalate only when quality, citation, or evidence gates fail.",
            ),
            ForecastProfile(
                task="pdf",
                display_name="Large PDF and final review",
                monthly_units=80,
                prompt_tokens_per_unit=110_000,
                completion_tokens_per_unit=12_000,
                expected_escalation_rate=0.0,
                baseline_model_alias="auto-pdf",
                rationale="Large PDFs are already premium exceptions; forecast keeps them explicit instead of hiding cost.",
            ),
        )

    def _forecast_row(self, profile: ForecastProfile) -> dict[str, Any]:
        escalation_plan = ModelEscalationPolicyService().evaluate(profile.task)
        initial_model = resolve_model("auto-fast" if profile.task == "classification" else None, task=profile.task)
        if escalation_plan.get("next_step"):
            initial_model = str(escalation_plan["next_step"]["resolved_model"])
        escalation_model = self._escalation_model(profile.task)
        baseline_model = resolve_model(profile.baseline_model_alias, task=profile.task)

        initial_unit_cost = estimate_token_cost_usd(
            initial_model,
            profile.prompt_tokens_per_unit,
            profile.completion_tokens_per_unit,
        )
        escalation_unit_cost = estimate_token_cost_usd(
            escalation_model,
            profile.prompt_tokens_per_unit,
            profile.completion_tokens_per_unit,
        )
        baseline_unit_cost = estimate_token_cost_usd(
            baseline_model,
            profile.prompt_tokens_per_unit,
            profile.completion_tokens_per_unit,
        )

        cheap_first_monthly = _cascade_monthly_cost(
            initial_unit_cost,
            escalation_unit_cost,
            profile.monthly_units,
            profile.expected_escalation_rate,
        )
        baseline_monthly = _monthly_cost(baseline_unit_cost, profile.monthly_units)

        return {
            "profile": profile.to_api(),
            "task": profile.task,
            "initial_model": initial_model,
            "escalation_model": escalation_model,
            "premium_baseline_model": baseline_model,
            "initial_unit_cost_usd": initial_unit_cost,
            "escalation_unit_cost_usd": escalation_unit_cost,
            "premium_baseline_unit_cost_usd": baseline_unit_cost,
            "cheap_first_monthly_cost_usd": cheap_first_monthly,
            "premium_baseline_monthly_cost_usd": baseline_monthly,
            "estimated_savings_ratio": _savings_ratio(cheap_first_monthly, baseline_monthly),
            "estimated_savings_usd": _savings_usd(cheap_first_monthly, baseline_monthly),
            "recommended_action": self._recommended_action(profile, cheap_first_monthly, baseline_monthly),
        }

    def _escalation_model(self, task: str) -> str:
        result = ModelEscalationPolicyService().evaluate(task, ["quality_gate_fail"])
        next_step = result.get("next_step") or {}
        if isinstance(next_step, dict) and next_step.get("resolved_model"):
            return str(next_step["resolved_model"])
        if task == "pdf":
            return task_default_model("pdf")
        return premium_text_model()

    def _recommended_action(
        self,
        profile: ForecastProfile,
        cheap_first_monthly: float | None,
        baseline_monthly: float | None,
    ) -> str:
        savings = _savings_ratio(cheap_first_monthly, baseline_monthly)
        if cheap_first_monthly is None or baseline_monthly is None:
            return "Add catalog pricing before using this profile for budget decisions."
        if profile.task == "pdf":
            return "Keep large PDF review as an explicit premium exception and monitor volume."
        if savings is not None and savings >= 0.5:
            return "Keep cheap-first routing; premium-only baseline is materially more expensive."
        return "Review task profile assumptions or escalation rate before changing defaults."


def _monthly_cost(unit_cost: float | None, monthly_units: int) -> float | None:
    if unit_cost is None:
        return None
    return round(unit_cost * max(0, monthly_units), 6)


def _cascade_monthly_cost(
    initial_unit_cost: float | None,
    escalation_unit_cost: float | None,
    monthly_units: int,
    escalation_rate: float,
) -> float | None:
    if initial_unit_cost is None or escalation_unit_cost is None:
        return None
    units = max(0, monthly_units)
    rate = max(0.0, min(1.0, escalation_rate))
    return round(units * initial_unit_cost + units * rate * escalation_unit_cost, 6)


def _savings_ratio(cheap_first_cost: float | None, baseline_cost: float | None) -> float | None:
    if cheap_first_cost is None or baseline_cost is None or baseline_cost <= 0:
        return None
    return round(max(0.0, (baseline_cost - cheap_first_cost) / baseline_cost), 4)


def _savings_usd(cheap_first_cost: float | None, baseline_cost: float | None) -> float | None:
    if cheap_first_cost is None or baseline_cost is None:
        return None
    return round(max(0.0, baseline_cost - cheap_first_cost), 6)
