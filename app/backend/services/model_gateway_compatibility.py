from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_catalog import (
    balanced_text_model,
    canonical_model_id,
    cheap_text_model,
    image_model,
    model_profile,
    premium_text_model,
    task_default_model,
)


@dataclass(frozen=True)
class GatewayModelRole:
    id: str
    label: str
    model: str
    env_var: str
    max_cost_tier: str
    should_be_gemini: bool = True


GATEWAY_EXAMPLES: tuple[str, ...] = (
    "gemini-2.5-flash-lite",
    "models/gemini-2.5-flash-lite",
    "google/gemini-2.5-flash-lite",
    "openrouter/google/gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "models/gemini-2.5-pro",
)


class ModelGatewayCompatibilityService:
    """Check whether configured Gemini/NewAPI names map to local cost metadata."""

    def evaluate(self) -> dict[str, Any]:
        role_checks = [self._role_check(role) for role in self._roles()]
        example_checks = [self._example_check(example) for example in GATEWAY_EXAMPLES]
        status = self._status(role_checks + example_checks)
        warnings = [check for check in role_checks + example_checks if check["status"] == "warn"]
        blocking = [check for check in role_checks + example_checks if check["status"] == "fail"]
        return {
            "status": status,
            "method": {
                "type": "gateway-model-name-compatibility",
                "notes": [
                    "Recognizes common OpenAI-compatible gateway prefixes for Gemini model ids.",
                    "Keeps gateway-specific unknown Gemini names pass-through but warns until pricing is cataloged.",
                    "Does not call external gateways and does not read API keys, prompts, documents, users, or raw output.",
                ],
            },
            "summary": {
                "configured_role_count": len(role_checks),
                "example_count": len(example_checks),
                "known_configured_count": sum(1 for check in role_checks if check["is_known_model"]),
                "prefixed_configured_count": sum(1 for check in role_checks if check["is_gateway_prefixed"]),
                "unknown_gemini_count": sum(1 for check in role_checks if check["is_gemini_like"] and not check["is_known_model"]),
                "non_gemini_default_count": sum(1 for check in role_checks if not check["is_gemini_like"]),
                "warning_count": len(warnings),
                "blocking_count": len(blocking),
            },
            "configured_roles": role_checks,
            "gateway_examples": example_checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(role_checks + example_checks),
        }

    def _roles(self) -> tuple[GatewayModelRole, ...]:
        return (
            GatewayModelRole("cheap-model", "Cheap text model", cheap_text_model(), "APP_AI_CHEAP_MODEL", "low"),
            GatewayModelRole("fast-model", "Fast route model", task_default_model("fast"), "APP_AI_FAST_MODEL", "low"),
            GatewayModelRole("ocr-model", "OCR route model", task_default_model("ocr"), "APP_OCR_MODEL", "low"),
            GatewayModelRole(
                "classification-model",
                "Classification route model",
                task_default_model("classification"),
                "APP_AI_CLASSIFIER_MODEL",
                "low",
            ),
            GatewayModelRole("review-model", "Review route model", task_default_model("review"), "APP_AI_REVIEW_MODEL", "medium"),
            GatewayModelRole("pdf-model", "PDF route model", task_default_model("pdf"), "APP_AI_PDF_MODEL", "premium"),
            GatewayModelRole("image-model", "Image route model", image_model(), "APP_AI_IMAGE_MODEL", "premium"),
            GatewayModelRole("balanced-model", "Balanced text model", balanced_text_model(), "APP_AI_BALANCED_MODEL", "medium"),
            GatewayModelRole("premium-model", "Premium text model", premium_text_model(), "APP_AI_PREMIUM_MODEL", "premium"),
        )

    def _role_check(self, role: GatewayModelRole) -> dict[str, Any]:
        canonical = canonical_model_id(role.model)
        profile = model_profile(role.model)
        normalized = role.model.strip().lower()
        is_gemini_like = bool(profile and profile.family == "gemini") or "gemini" in normalized
        is_gateway_prefixed = bool(canonical and canonical != normalized)
        status = "pass"
        reasons: list[str] = []
        if role.should_be_gemini and not is_gemini_like:
            status = "fail"
            reasons.append("Configured default is not recognizably Gemini-compatible.")
        elif profile is None:
            status = "warn"
            reasons.append("Model looks gateway-specific; add catalog pricing and capabilities before using it as a default.")
        elif _tier_rank(profile.cost_tier) > _tier_rank(role.max_cost_tier):
            status = "fail"
            reasons.append(f"Resolved cost tier {profile.cost_tier} exceeds max {role.max_cost_tier}.")
        elif is_gateway_prefixed:
            reasons.append(f"Gateway-prefixed name resolves to catalog model {canonical}.")
        else:
            reasons.append("Configured model resolves directly to local Gemini catalog metadata.")

        return {
            "id": role.id,
            "label": role.label,
            "env_var": role.env_var,
            "model": role.model,
            "canonical_model": canonical,
            "is_known_model": profile is not None,
            "is_gemini_like": is_gemini_like,
            "is_gateway_prefixed": is_gateway_prefixed,
            "cost_tier": profile.cost_tier if profile else None,
            "max_cost_tier": role.max_cost_tier,
            "status": status,
            "reason": " ".join(reasons),
        }

    def _example_check(self, model_name: str) -> dict[str, Any]:
        canonical = canonical_model_id(model_name)
        profile = model_profile(model_name)
        status = "pass" if profile else "warn"
        return {
            "id": f"gateway-example-{model_name.replace('/', '-').replace(':', '-')}",
            "model": model_name,
            "canonical_model": canonical,
            "is_known_model": profile is not None,
            "is_gateway_prefixed": bool(canonical and canonical != model_name.lower()),
            "status": status,
            "reason": (
                f"{model_name} resolves to {canonical}."
                if canonical
                else f"{model_name} remains pass-through until added to the local catalog."
            ),
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
            if check.get("is_gemini_like") and not check.get("is_known_model"):
                actions.append(f"Add catalog metadata for {check['model']} before making it a default.")
            elif not check.get("is_gemini_like", True):
                actions.append(f"Move {check.get('env_var', 'configured model')} back to a Gemini model name.")
            else:
                actions.append(f"Review gateway compatibility for {check['model']}.")
        if not actions:
            actions.append("Configured gateway model names resolve to Gemini catalog metadata.")
        return actions


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)
