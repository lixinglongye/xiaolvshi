from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import COST_TIER_RANK, TASK_GROUPS
from services.model_catalog import (
    GEMINI_MODEL_CATALOG,
    canonical_model_id,
    cheap_text_model,
    task_default_model,
)


DEPRECATED_MODEL_PREFIXES = (
    "gemini-1.0",
    "gemini-1.5",
    "gemini-2.0",
)
SCHEDULED_SHUTDOWN_REPLACEMENTS: dict[str, dict[str, str]] = {
    "gemini-2.5-flash-lite": {
        "replacement_model": "gemini-3.1-flash-lite",
        "shutdown_on": "2026-10-16",
        "migration_note": "Official deprecation guidance recommends Gemini 3.1 Flash-Lite as the Flash-Lite replacement.",
    },
    "gemini-2.5-flash": {
        "replacement_model": "gemini-3.5-flash",
        "shutdown_on": "2026-10-16",
        "migration_note": "Official deprecation guidance recommends Gemini 3.5 Flash as the Flash replacement.",
    },
}
UNSTABLE_ALIAS_SUFFIXES = (
    "-latest",
    "-preview",
)


@dataclass(frozen=True)
class ConfiguredModelRole:
    role: str
    model: str
    task: str
    max_cost_tier: str
    canonical_model: str | None
    lifecycle_state: str
    cost_tier: str | None
    model_status: str
    default_allowed: bool
    cheap_first_aligned: bool
    replacement_model: str | None
    scheduled_shutdown_on: str | None
    migration_note: str | None
    reason: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class ModelLifecyclePolicyService:
    """Audit Gemini model lifecycle choices for stable cheap-first defaults."""

    def build_policy(self) -> dict[str, Any]:
        roles = [self._configured_role(role, task) for role, task in self._role_tasks()]
        checks = self._checks(roles)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        return {
            "status": "fail" if blocking else ("warn" if warnings else "pass"),
            "method": {
                "type": "gemini-model-lifecycle-policy",
                "notes": [
                    "Stable catalog models may be used as defaults when they fit the task budget.",
                    "Preview and latest aliases are allowed for explicit experiments, not unattended defaults.",
                    "Deprecated Gemini 1.x/2.0 style models are not allowed as defaults.",
                    "Gateway-prefixed model names are canonicalized before lifecycle checks.",
                ],
                "source_urls": [
                    "https://ai.google.dev/gemini-api/docs/models",
                    "https://ai.google.dev/gemini-api/docs/pricing",
                    "https://ai.google.dev/gemini-api/docs/openai",
                ],
            },
            "summary": {
                "catalog_model_count": len(GEMINI_MODEL_CATALOG),
                "stable_catalog_count": sum(1 for item in GEMINI_MODEL_CATALOG if item.status == "stable"),
                "preview_catalog_count": sum(1 for item in GEMINI_MODEL_CATALOG if item.status == "preview"),
                "review_catalog_count": sum(1 for item in GEMINI_MODEL_CATALOG if item.status == "review"),
                "scheduled_shutdown_replacement_count": len(SCHEDULED_SHUTDOWN_REPLACEMENTS),
                "configured_role_count": len(roles),
                "default_allowed_count": sum(1 for role in roles if role.default_allowed),
                "configured_scheduled_shutdown_count": sum(1 for role in roles if role.scheduled_shutdown_on),
                "preview_default_count": sum(1 for role in roles if role.lifecycle_state == "preview"),
                "review_default_count": sum(1 for role in roles if role.lifecycle_state == "review"),
                "deprecated_default_count": sum(1 for role in roles if role.lifecycle_state == "deprecated"),
                "latest_alias_default_count": sum(1 for role in roles if role.lifecycle_state == "unstable_alias"),
                "unknown_default_count": sum(1 for role in roles if role.lifecycle_state == "unknown"),
                "cheap_first_aligned_count": sum(1 for role in roles if role.cheap_first_aligned),
            },
            "configured_roles": [role.to_api() for role in roles],
            "catalog_lifecycle": self._catalog_lifecycle(),
            "alias_policy": self._alias_policy(),
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "checks": checks,
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "privacy_note": (
                "Lifecycle checks inspect model IDs, roles, task budgets, and public documentation links only. "
                "They never store API keys, prompts, documents, user identifiers, emails, or model outputs."
            ),
        }

    def _role_tasks(self) -> tuple[tuple[str, str], ...]:
        return (
            ("cheap", "cheap"),
            ("balanced", "review"),
            ("premium", "pdf"),
            ("fast", "fast"),
            ("ocr", "ocr"),
            ("classification", "classification"),
            ("review", "review"),
            ("grounded-research", "grounded-research"),
            ("agentic", "agentic"),
            ("pdf", "pdf"),
        )

    def _configured_role(self, role: str, task: str) -> ConfiguredModelRole:
        model = cheap_text_model() if role == "cheap" else task_default_model(task)
        canonical = canonical_model_id(model)
        profile = next((item for item in GEMINI_MODEL_CATALOG if item.id == canonical), None)
        lifecycle_state = self._lifecycle_state(model, profile.status if profile else None)
        replacement = SCHEDULED_SHUTDOWN_REPLACEMENTS.get(canonical or "")
        cost_tier = profile.cost_tier if profile else None
        max_cost_tier = str(TASK_GROUPS.get(task, {}).get("max_cost_tier", "premium"))
        default_allowed = self._default_allowed(lifecycle_state, cost_tier, max_cost_tier, task)
        cheap_first_aligned = self._cheap_first_aligned(role, cost_tier, task)
        return ConfiguredModelRole(
            role=role,
            model=model,
            task=task,
            max_cost_tier=max_cost_tier,
            canonical_model=canonical,
            lifecycle_state=lifecycle_state,
            cost_tier=cost_tier,
            model_status=profile.status if profile else "unknown",
            default_allowed=default_allowed,
            cheap_first_aligned=cheap_first_aligned,
            replacement_model=replacement.get("replacement_model") if replacement else None,
            scheduled_shutdown_on=replacement.get("shutdown_on") if replacement else None,
            migration_note=replacement.get("migration_note") if replacement else None,
            reason=self._role_reason(
                lifecycle_state=lifecycle_state,
                default_allowed=default_allowed,
                cheap_first_aligned=cheap_first_aligned,
                cost_tier=cost_tier,
                max_cost_tier=max_cost_tier,
            ),
        )

    def _lifecycle_state(self, model: str, status: str | None) -> str:
        value = (model or "").strip().lower()
        canonical = canonical_model_id(value)
        check_value = canonical or value.rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        if any(check_value.startswith(prefix) for prefix in DEPRECATED_MODEL_PREFIXES):
            return "deprecated"
        if status == "preview":
            return "preview"
        if status == "review":
            return "review"
        if status == "stable":
            return "stable"
        if any(check_value.endswith(suffix) for suffix in UNSTABLE_ALIAS_SUFFIXES):
            return "unstable_alias"
        return "unknown"

    def _default_allowed(self, lifecycle_state: str, cost_tier: str | None, max_cost_tier: str, task: str) -> bool:
        if lifecycle_state != "stable":
            return False
        if task in {"pdf", "image"}:
            return True
        return COST_TIER_RANK.get(cost_tier or "unknown", 99) <= COST_TIER_RANK.get(max_cost_tier, 99)

    def _cheap_first_aligned(self, role: str, cost_tier: str | None, task: str) -> bool:
        if role in {"cheap", "fast", "ocr", "classification", "agentic"}:
            return cost_tier in {"lowest", "low"}
        if role == "grounded-research":
            return cost_tier in {"lowest", "low"}
        if task == "review":
            return cost_tier in {"lowest", "low", "medium"}
        if task == "pdf":
            return cost_tier == "premium"
        return True

    def _role_reason(
        self,
        *,
        lifecycle_state: str,
        default_allowed: bool,
        cheap_first_aligned: bool,
        cost_tier: str | None,
        max_cost_tier: str,
    ) -> str:
        if not default_allowed:
            if lifecycle_state == "deprecated":
                return "Deprecated Gemini generation should be removed from defaults."
            if lifecycle_state in {"preview", "unstable_alias"}:
                return "Preview/latest model aliases require explicit maintainer experiments before default use."
            if lifecycle_state == "review":
                return "Review-only model ids require maintainer approval before default use."
            if lifecycle_state == "unknown":
                return "Gateway model is not in the local catalog; verify lifecycle and pricing before default use."
            return "Model lifecycle or cost tier is not allowed for this default."
        if not cheap_first_aligned:
            return f"Model is stable but cost tier {cost_tier or 'unknown'} exceeds cheap-first expectations."
        return f"Stable default is within the task cost budget ({cost_tier or 'unknown'} <= {max_cost_tier})."

    def _checks(self, roles: list[ConfiguredModelRole]) -> list[dict[str, Any]]:
        deprecated = [role.role for role in roles if role.lifecycle_state == "deprecated"]
        unstable = [role.role for role in roles if role.lifecycle_state in {"preview", "unstable_alias"}]
        review_only = [role.role for role in roles if role.lifecycle_state == "review"]
        unknown = [role.role for role in roles if role.lifecycle_state == "unknown"]
        disallowed = [role.role for role in roles if not role.default_allowed]
        cheap_drift = [
            role.role
            for role in roles
            if role.role in {"cheap", "fast", "ocr", "classification", "grounded-research", "agentic"}
            and role.cost_tier is not None
            and not role.cheap_first_aligned
        ]
        return [
            {
                "id": "no-deprecated-defaults",
                "status": "fail" if deprecated else "pass",
                "reason": "Deprecated Gemini generations are not configured as defaults."
                if not deprecated
                else f"Deprecated Gemini defaults found: {', '.join(deprecated)}.",
            },
            {
                "id": "preview-default-review",
                "status": "warn" if unstable or review_only else "pass",
                "reason": "No preview or latest aliases are configured as unattended defaults."
                if not unstable and not review_only
                else "Preview/latest/review-only defaults require review: "
                + ", ".join(unstable + review_only)
                + ".",
            },
            {
                "id": "known-default-lifecycle",
                "status": "warn" if unknown else "pass",
                "reason": "All configured defaults map to known lifecycle states."
                if not unknown
                else f"Unknown lifecycle defaults require catalog review: {', '.join(unknown)}.",
            },
            {
                "id": "default-allow-list",
                "status": "fail" if any(role in deprecated for role in disallowed) else ("warn" if disallowed else "pass"),
                "reason": "All defaults satisfy lifecycle and task budget allow-list rules."
                if not disallowed
                else f"Defaults outside allow-list: {', '.join(disallowed)}.",
            },
            {
                "id": "cheap-role-cost-tier",
                "status": "fail" if cheap_drift else "pass",
                "reason": "Cheap/high-volume roles are aligned with lowest or low cost tiers."
                if not cheap_drift
                else f"Cheap/high-volume roles drifted from low-cost models: {', '.join(cheap_drift)}.",
            },
        ]

    def _catalog_lifecycle(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for profile in GEMINI_MODEL_CATALOG:
            replacement = SCHEDULED_SHUTDOWN_REPLACEMENTS.get(profile.id)
            rows.append(
                {
                    "model": profile.id,
                    "status": profile.status,
                    "cost_tier": profile.cost_tier,
                    "replacement_model": replacement.get("replacement_model") if replacement else None,
                    "scheduled_shutdown_on": replacement.get("shutdown_on") if replacement else None,
                    "migration_note": replacement.get("migration_note") if replacement else None,
                    "default_policy": "allowed_when_task_budget_fits"
                    if profile.status == "stable"
                    else "explicit_experiment_only",
                    "preferred_default_role": self._preferred_default_role(profile.cost_tier, profile.status),
                    "pricing_source_url": profile.pricing_source_url,
                }
            )
        return rows

    def _preferred_default_role(self, cost_tier: str, status: str) -> str:
        if status != "stable":
            return "none"
        if cost_tier in {"lowest", "low"}:
            return "cheap_or_balanced"
        if cost_tier == "medium":
            return "review_only_after_cost_check"
        return "premium_exception_only"

    def _alias_policy(self) -> dict[str, Any]:
        return {
            "canonical_prefixes": ["models/", "google/", "openrouter/google/", "provider/google/"],
            "pass_through": "Unknown gateway model IDs may pass through request routing, but are not lifecycle-approved defaults.",
            "latest_alias_default_policy": "Do not use latest aliases as defaults; pin a concrete model ID after validation.",
            "deprecated_generations": list(DEPRECATED_MODEL_PREFIXES),
            "scheduled_shutdown_replacements": dict(SCHEDULED_SHUTDOWN_REPLACEMENTS),
            "stable_default_examples": [
                "gemini-2.5-flash-lite",
                "gemini-2.5-flash",
                "gemini-2.5-pro",
            ],
        }

    def _recommended_actions(self, blocking: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
        if blocking:
            return [
                "Replace deprecated or disallowed Gemini defaults before release.",
                "Keep cheap, fast, OCR, and classification defaults on stable lowest/low cost models.",
            ]
        if warnings:
            return [
                "Review preview, latest, or unknown gateway model defaults before promoting them.",
                "Pin concrete Gemini model IDs after validating NewAPI/Gemini gateway support and pricing.",
            ]
        return [
            "Gemini defaults are stable and cheap-first aligned.",
            "Keep preview/latest aliases as explicit experiments until maintainer review approves them.",
        ]
