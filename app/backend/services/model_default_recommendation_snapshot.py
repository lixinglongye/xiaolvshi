from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_catalog import (
    GEMINI_MODEL_CATALOG,
    canonical_model_id,
    model_profile,
    task_default_model,
)


@dataclass(frozen=True)
class DefaultRoleTarget:
    role: str
    task: str
    env_var: str
    required_capabilities: tuple[str, ...]
    max_cost_tier: str
    high_volume: bool
    operator_review_required: bool

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_capabilities"] = list(self.required_capabilities)
        return data


ROLE_TARGETS: tuple[DefaultRoleTarget, ...] = (
    DefaultRoleTarget("cheap", "cheap", "APP_AI_CHEAP_MODEL", ("text", "json"), "lowest", True, False),
    DefaultRoleTarget("fast", "fast", "APP_AI_FAST_MODEL", ("text", "json"), "lowest", True, False),
    DefaultRoleTarget("classification", "classification", "APP_AI_CLASSIFIER_MODEL", ("text", "json", "classification"), "lowest", True, False),
    DefaultRoleTarget("ocr", "ocr", "APP_OCR_MODEL", ("text", "vision", "ocr"), "lowest", True, False),
    DefaultRoleTarget("review", "review", "APP_AI_REVIEW_MODEL", ("text", "json", "review"), "low", False, False),
    DefaultRoleTarget("grounded-research", "grounded-research", "APP_AI_GROUNDED_RESEARCH_MODEL", ("text", "grounding"), "low", True, False),
    DefaultRoleTarget("agentic", "agentic", "APP_AI_AGENTIC_MODEL", ("text", "agentic"), "low", True, False),
    DefaultRoleTarget("pdf", "pdf", "APP_AI_PDF_MODEL", ("text", "vision", "long-context"), "premium", False, True),
)


class ModelDefaultRecommendationSnapshotService:
    """Summarize current Gemini/NewAPI defaults against cheap-first role targets."""

    def build_snapshot(self, observed_models: list[Any] | None = None) -> dict[str, Any]:
        role_rows = [self._role_row(target) for target in ROLE_TARGETS]
        observed_rows = [self._observed_row(model_id) for model_id in self._observed_model_ids(observed_models)]
        blocking = [row for row in role_rows if row["status"] == "fail"]
        warnings = [row for row in role_rows if row["status"] == "warn"]
        catalog_review = [row for row in observed_rows if row["status"] == "catalog_review"]

        return {
            "status": "fail" if blocking else ("warn" if warnings or catalog_review else "pass"),
            "method": {
                "type": "gemini-newapi-default-recommendation-snapshot",
                "notes": [
                    "Checks local default model roles only; it never calls NewAPI, Gemini, or any OpenAI-compatible gateway.",
                    "High-volume roles must stay on stable lowest-tier Gemini models unless an operator explicitly changes policy.",
                    "Observed gateway model IDs are sanitized metadata used only for catalog review and prefix compatibility checks.",
                ],
            },
            "summary": {
                "role_count": len(role_rows),
                "high_volume_role_count": sum(1 for row in role_rows if row["high_volume"]),
                "blocking_count": len(blocking),
                "warning_count": len(warnings),
                "observed_model_count": len(observed_rows),
                "catalog_review_count": len(catalog_review),
                "cheap_first_ready": not blocking,
            },
            "role_targets": [target.to_api() for target in ROLE_TARGETS],
            "role_recommendations": role_rows,
            "observed_gateway_models": observed_rows,
            "blocked_default_roles": [row["role"] for row in blocking],
            "catalog_review_models": [row["model"] for row in catalog_review],
            "newapi_prefix_compatibility": [
                "gemini-2.5-flash-lite",
                "models/gemini-2.5-flash-lite",
                "google/gemini-2.5-flash-lite",
                "openrouter/google/gemini-2.5-flash-lite",
            ],
            "recommended_env": [
                {
                    "env_var": row["env_var"],
                    "recommended_model": row["recommended_model"],
                    "current_model": row["current_model"],
                    "requires_change": row["requires_change"],
                    "reason": row["reason"],
                }
                for row in role_rows
                if row["env_var"]
            ],
            "release_guardrails": [
                "Do not set Pro, preview, image, or unknown models as fast, classification, OCR, or cheap defaults.",
                "Do not promote unknown Gemini-like NewAPI model IDs until local pricing, lifecycle, and capability metadata are added.",
                "Keep premium PDF/final-review routes behind operator review and explicit task routing.",
            ],
            "validation_commands": [
                "python -m pytest tests/test_model_default_recommendation_snapshot.py -q",
                "python -m pytest tests/test_model_catalog.py tests/test_model_default_optimization.py -q",
            ],
            "privacy_note": (
                "The snapshot stores model names, roles, cost tiers, and capability metadata only. It never stores "
                "API keys, prompts, uploaded documents, raw gateway responses, user identifiers, or contact details."
            ),
        }

    def _role_row(self, target: DefaultRoleTarget) -> dict[str, Any]:
        current_model = task_default_model(target.task)
        profile = model_profile(current_model)
        recommended_model = self._recommended_model(target)
        current_cost_tier = profile.cost_tier if profile else None
        current_status = profile.status if profile else "unknown"
        missing_capabilities = self._missing_capabilities(profile, target.required_capabilities)
        over_budget = _tier_rank(current_cost_tier) > _tier_rank(target.max_cost_tier)
        high_volume_bad_default = target.high_volume and (
            _tier_rank(current_cost_tier) > _tier_rank(target.max_cost_tier)
            or current_status != "stable"
            or self._looks_premium_or_preview(current_model)
        )
        status = "pass"
        if profile is None or missing_capabilities:
            status = "warn"
        if over_budget or high_volume_bad_default:
            status = "fail"
        return {
            "id": f"default-recommendation-{target.role}",
            "role": target.role,
            "task": target.task,
            "env_var": target.env_var,
            "current_model": current_model,
            "canonical_model": canonical_model_id(current_model),
            "recommended_model": recommended_model,
            "requires_change": current_model != recommended_model,
            "high_volume": target.high_volume,
            "operator_review_required": target.operator_review_required,
            "required_capabilities": list(target.required_capabilities),
            "missing_required_capabilities": missing_capabilities,
            "max_cost_tier": target.max_cost_tier,
            "current_cost_tier": current_cost_tier,
            "model_status": current_status,
            "status": status,
            "reason": self._role_reason(
                profile=profile,
                target=target,
                current_model=current_model,
                recommended_model=recommended_model,
                missing_capabilities=missing_capabilities,
                over_budget=over_budget,
                high_volume_bad_default=high_volume_bad_default,
            ),
        }

    def _observed_row(self, model_id: str) -> dict[str, Any]:
        canonical = canonical_model_id(model_id)
        profile = model_profile(model_id)
        is_gemini_like = "gemini" in model_id.lower()
        status = "known" if profile else ("catalog_review" if is_gemini_like else "pass_through")
        return {
            "model": model_id,
            "canonical_model": canonical,
            "status": status,
            "is_known_model": profile is not None,
            "is_gemini_like": is_gemini_like,
            "cost_tier": profile.cost_tier if profile else None,
            "model_status": profile.status if profile else "unknown",
            "reason": "Known local catalog model."
            if profile
            else (
                "Gemini-like NewAPI model needs local pricing, lifecycle, and capability metadata before default use."
                if is_gemini_like
                else "Non-Gemini gateway model can pass through but should not become a default without review."
            ),
        }

    def _recommended_model(self, target: DefaultRoleTarget) -> str:
        candidates = []
        for profile in GEMINI_MODEL_CATALOG:
            if profile.status != "stable":
                continue
            if _tier_rank(profile.cost_tier) > _tier_rank(target.max_cost_tier):
                continue
            if set(target.required_capabilities).issubset(set(profile.capabilities)):
                candidates.append(profile)
        if not candidates:
            return task_default_model(target.task)
        return sorted(
            candidates,
            key=lambda item: (
                _tier_rank(item.cost_tier),
                item.latency_tier != "fastest",
                item.input_usd_per_million_tokens or 999,
                item.id,
            ),
        )[0].id

    def _missing_capabilities(self, profile: Any, required_capabilities: tuple[str, ...]) -> list[str]:
        if profile is None:
            return []
        return sorted(set(required_capabilities) - set(profile.capabilities))

    def _role_reason(
        self,
        *,
        profile: Any,
        target: DefaultRoleTarget,
        current_model: str,
        recommended_model: str,
        missing_capabilities: list[str],
        over_budget: bool,
        high_volume_bad_default: bool,
    ) -> str:
        if profile is None:
            return "Current model is unknown to the local Gemini catalog; pricing and lifecycle are unverified."
        if missing_capabilities:
            return f"Current model is missing required capabilities: {', '.join(missing_capabilities)}."
        if high_volume_bad_default:
            return f"{target.role} is high-volume and must use a stable lowest-tier model such as {recommended_model}."
        if over_budget:
            return f"Current model exceeds the {target.max_cost_tier} cost tier for {target.role}."
        if current_model != recommended_model:
            return f"Current model is allowed, but {recommended_model} is the cheaper capable recommendation."
        return f"{target.role} default is aligned with cheap-first Gemini routing."

    def _observed_model_ids(self, observed_models: list[Any] | None) -> list[str]:
        seen: set[str] = set()
        rows: list[str] = []
        for item in observed_models or []:
            if isinstance(item, str):
                model_id = item.strip()
            elif isinstance(item, dict):
                model_id = str(item.get("id") or item.get("model") or item.get("name") or "").strip()
            else:
                model_id = ""
            if not model_id or model_id in seen:
                continue
            seen.add(model_id)
            rows.append(model_id)
        return rows

    def _looks_premium_or_preview(self, model_id: str) -> bool:
        value = model_id.lower()
        return any(marker in value for marker in ("pro", "preview", "image"))


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)
