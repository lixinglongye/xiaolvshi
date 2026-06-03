from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_catalog import (
    balanced_text_model,
    cheap_text_model,
    model_profile,
    premium_text_model,
    task_default_model,
)


@dataclass(frozen=True)
class ConfiguredModelRole:
    id: str
    label: str
    model: str
    env_var: str | None
    max_cost_tier: str
    preferred_cost_tier: str | None
    required_capabilities: tuple[str, ...]
    preferred_capabilities: tuple[str, ...]
    rationale: str


class ModelConfigurationAuditService:
    """Audit configured model roles against the cheap-first routing policy."""

    def audit(self) -> dict[str, Any]:
        checks = [self._audit_role(role) for role in self._configured_roles()]
        status = self._status(checks)
        return {
            "status": status,
            "method": {
                "type": "configured-model-role-audit",
                "notes": [
                    "Evaluates resolved model role configuration without reading API keys or prompts.",
                    "Unknown gateway model names remain allowed but are warned until catalog pricing and capabilities are verified.",
                    "High-volume cheap, OCR, and classification roles fail if configured above their cost ceiling or missing required capabilities.",
                ],
            },
            "summary": {
                "role_count": len(checks),
                "pass_count": sum(1 for check in checks if check["status"] == "pass"),
                "warn_count": sum(1 for check in checks if check["status"] == "warn"),
                "fail_count": sum(1 for check in checks if check["status"] == "fail"),
                "unknown_model_count": sum(1 for check in checks if not check["is_known_model"]),
                "premium_default_count": sum(1 for check in checks if check.get("cost_tier") == "premium"),
            },
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in checks if check["status"] == "fail"],
            "warning_check_ids": [check["id"] for check in checks if check["status"] == "warn"],
            "recommended_actions": self._recommended_actions(checks),
        }

    def _configured_roles(self) -> list[ConfiguredModelRole]:
        cheap = cheap_text_model()
        balanced = balanced_text_model()
        premium = premium_text_model()
        return [
            ConfiguredModelRole(
                id="cheap-model-role",
                label="Cheap text model",
                model=cheap,
                env_var="APP_AI_CHEAP_MODEL",
                max_cost_tier="low",
                preferred_cost_tier="lowest",
                required_capabilities=("text", "json"),
                preferred_capabilities=("classification", "ocr"),
                rationale="High-volume fallback role should stay on the cheapest capable Gemini text model.",
            ),
            ConfiguredModelRole(
                id="fast-route-model",
                label="Fast task default",
                model=task_default_model("fast"),
                env_var="APP_AI_FAST_MODEL or APP_AI_CHEAP_MODEL",
                max_cost_tier="low",
                preferred_cost_tier="lowest",
                required_capabilities=("text", "json"),
                preferred_capabilities=("classification",),
                rationale="Fast preflight and routing tasks should not default to premium models.",
            ),
            ConfiguredModelRole(
                id="ocr-route-model",
                label="OCR task default",
                model=task_default_model("ocr"),
                env_var="APP_OCR_MODEL or APP_AI_CHEAP_MODEL",
                max_cost_tier="low",
                preferred_cost_tier="lowest",
                required_capabilities=("text", "vision"),
                preferred_capabilities=("ocr",),
                rationale="OCR can run on many pages, so the configured model must stay cheap and vision-capable.",
            ),
            ConfiguredModelRole(
                id="classification-route-model",
                label="Classification task default",
                model=task_default_model("classification"),
                env_var="APP_AI_CLASSIFIER_MODEL or APP_AI_CHEAP_MODEL",
                max_cost_tier="low",
                preferred_cost_tier="lowest",
                required_capabilities=("text", "json"),
                preferred_capabilities=("classification",),
                rationale="Classification is high-volume and should remain cheap, deterministic, and structured.",
            ),
            ConfiguredModelRole(
                id="balanced-model-role",
                label="Balanced text model",
                model=balanced,
                env_var="APP_AI_BALANCED_MODEL",
                max_cost_tier="medium",
                preferred_cost_tier="low",
                required_capabilities=("text", "json"),
                preferred_capabilities=("review",),
                rationale="Balanced role may spend more than cheap routing but should avoid premium defaults.",
            ),
            ConfiguredModelRole(
                id="review-route-model",
                label="Review task default",
                model=task_default_model("review"),
                env_var="APP_AI_REVIEW_MODEL or APP_AI_BALANCED_MODEL",
                max_cost_tier="medium",
                preferred_cost_tier="low",
                required_capabilities=("text", "json"),
                preferred_capabilities=("review",),
                rationale="Legal review needs stronger analysis but should not silently become premium.",
            ),
            ConfiguredModelRole(
                id="premium-model-role",
                label="Premium text model",
                model=premium,
                env_var="APP_AI_PREMIUM_MODEL",
                max_cost_tier="premium",
                preferred_cost_tier="premium",
                required_capabilities=("text",),
                preferred_capabilities=("long-context", "complex-reasoning"),
                rationale="Premium role should be reserved for hard legal reasoning and final review exceptions.",
            ),
            ConfiguredModelRole(
                id="pdf-route-model",
                label="PDF task default",
                model=task_default_model("pdf"),
                env_var="APP_AI_PDF_MODEL or APP_AI_PREMIUM_MODEL",
                max_cost_tier="premium",
                preferred_cost_tier="premium",
                required_capabilities=("text",),
                preferred_capabilities=("long-context", "complex-reasoning"),
                rationale="PDF route may use premium context, but missing long-context capability should be visible.",
            ),
        ]

    def _audit_role(self, role: ConfiguredModelRole) -> dict[str, Any]:
        profile = model_profile(role.model)
        cost_tier = profile.cost_tier if profile else None
        capabilities = set(profile.capabilities) if profile else set()
        missing_required = sorted(set(role.required_capabilities) - capabilities)
        missing_preferred = sorted(set(role.preferred_capabilities) - capabilities)
        over_budget = _tier_rank(cost_tier) > _tier_rank(role.max_cost_tier) if cost_tier else False

        status = "pass"
        reasons: list[str] = []
        if profile is None:
            status = "warn"
            reasons.append("Configured model is not in the local catalog; pricing and capabilities are unverified.")
        elif over_budget or missing_required:
            status = "fail"
            if over_budget:
                reasons.append(f"Cost tier {cost_tier} exceeds max {role.max_cost_tier}.")
            if missing_required:
                reasons.append(f"Missing required capabilities: {', '.join(missing_required)}.")
        elif (
            role.preferred_cost_tier
            and cost_tier != role.preferred_cost_tier
            and _tier_rank(cost_tier) <= _tier_rank(role.max_cost_tier)
        ):
            status = "warn"
            reasons.append(f"Cost tier {cost_tier} is allowed but not preferred {role.preferred_cost_tier}.")
        elif missing_preferred:
            status = "warn"
            reasons.append(f"Missing preferred capabilities: {', '.join(missing_preferred)}.")

        if not reasons:
            reasons.append("Configured model role matches cost and capability expectations.")

        return {
            "id": role.id,
            "status": status,
            "label": role.label,
            "model": role.model,
            "env_var": role.env_var,
            "is_known_model": profile is not None,
            "cost_tier": cost_tier,
            "max_cost_tier": role.max_cost_tier,
            "preferred_cost_tier": role.preferred_cost_tier,
            "required_capabilities": list(role.required_capabilities),
            "preferred_capabilities": list(role.preferred_capabilities),
            "missing_required_capabilities": missing_required,
            "missing_preferred_capabilities": missing_preferred,
            "over_budget": over_budget,
            "rationale": role.rationale,
            "reason": " ".join(reasons),
        }

    def _status(self, checks: list[dict[str, Any]]) -> str:
        if any(check["status"] == "fail" for check in checks):
            return "fail"
        if any(check["status"] == "warn" for check in checks):
            return "warn"
        return "pass"

    def _recommended_actions(self, checks: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        for check in checks:
            if check["status"] == "pass":
                continue
            if not check["is_known_model"]:
                actions.append(f"Add {check['model']} to model_catalog.py or document why {check['label']} uses an unverified gateway model.")
            elif check["over_budget"]:
                actions.append(f"Move {check['label']} back to a model at or below {check['max_cost_tier']} cost tier.")
            elif check["missing_required_capabilities"]:
                actions.append(f"Choose a model for {check['label']} with required capabilities: {', '.join(check['missing_required_capabilities'])}.")
            else:
                actions.append(f"Review {check['label']} because it is acceptable but not the preferred cheap-first fit.")
        if not actions:
            actions.append("Configured model roles match cheap-first cost and capability expectations.")
        return actions


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)
