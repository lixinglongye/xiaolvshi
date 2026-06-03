from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from services.model_catalog import GEMINI_MODEL_CATALOG, canonical_model_id, model_profile


HIGH_FREQUENCY_TASKS = (
    "fast",
    "routing",
    "triage",
    "classification",
    "ocr",
    "batch_summary",
    "quote_extraction",
)

PREMIUM_DEFAULT_MARKERS = ("pro", "preview", "premium")


@dataclass(frozen=True)
class GeminiModelFamily:
    family: str
    catalog_patterns: tuple[str, ...]
    catalog_models: tuple[str, ...]
    cost_posture: str
    default_use: str
    high_frequency_default_allowed: bool
    notes: str

    def to_api(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "catalog_patterns": list(self.catalog_patterns),
            "catalog_models": list(self.catalog_models),
            "cost_posture": self.cost_posture,
            "default_use": self.default_use,
            "high_frequency_default_allowed": self.high_frequency_default_allowed,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class TaskDefaultRecommendation:
    task: str
    recommended_model: str
    model_family: str
    cost_tier: str
    route_mode: str
    high_frequency: bool
    escalation_after: str
    rationale: str

    def to_api(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "recommended_model": self.recommended_model,
            "model_family": self.model_family,
            "cost_tier": self.cost_tier,
            "route_mode": self.route_mode,
            "high_frequency": self.high_frequency,
            "escalation_after": self.escalation_after,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ObservedModelReview:
    raw_model: str
    normalized_model: str | None
    is_gemini_like: bool
    status: str
    severity: str
    action: str
    default_allowed_for_high_frequency: bool
    warnings: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        return {
            "raw_model": self.raw_model,
            "normalized_model": self.normalized_model,
            "is_gemini_like": self.is_gemini_like,
            "status": self.status,
            "severity": self.severity,
            "action": self.action,
            "default_allowed_for_high_frequency": self.default_allowed_for_high_frequency,
            "warnings": list(self.warnings),
        }


class GeminiNewapiCheapFirstPolicyService:
    """Catalog and default-selection policy for Gemini models behind NewAPI."""

    def build_policy(self, observed_models: Iterable[Any] | None = None) -> dict[str, Any]:
        model_reviews = [self._review_observed_model(item).to_api() for item in observed_models or ()]
        defaults = [item.to_api() for item in self._default_recommendations()]
        review_warnings = [
            item
            for item in model_reviews
            if item["severity"] == "warn" or item["status"] == "catalog_review"
        ]

        return {
            "status": "ready",
            "summary": {
                "default_posture": "cheap_first",
                "known_gemini_models": len(GEMINI_MODEL_CATALOG),
                "high_frequency_default_model": "gemini-2.5-flash-lite",
                "high_frequency_tasks": list(HIGH_FREQUENCY_TASKS),
                "catalog_review_count": len(review_warnings),
                "premium_default_blocked_for_high_frequency": True,
            },
            "supported_gemini_model_families": [item.to_api() for item in self._supported_families()],
            "newapi_openai_compatible_prefix_compatibility": self._prefix_compatibility(),
            "default_model_recommendations": defaults,
            "cheap_first_task_ladder": self._cheap_first_task_ladder(),
            "unknown_gemini_like_model_handling": self._unknown_model_policy(),
            "forbidden_default_rules": self._forbidden_default_rules(),
            "observed_model_review": model_reviews,
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_gemini_newapi_cheap_first_policy.py -q",
                "cd app/backend && python -m compileall services/gemini_newapi_cheap_first_policy.py tests/test_gemini_newapi_cheap_first_policy.py",
            ],
            "privacy_note": [
                "Policy output contains model routing metadata only.",
                "Do not persist raw prompts, uploaded documents, contact identifiers, or gateway credentials in this policy payload.",
                "Observed model ids are safe to log after caller-side redaction because they are catalog labels, not user content.",
            ],
        }

    def _supported_families(self) -> tuple[GeminiModelFamily, ...]:
        catalog_ids = tuple(item.id for item in GEMINI_MODEL_CATALOG)
        flash_lite_models = tuple(model for model in catalog_ids if "flash-lite" in model)
        flash_models = tuple(
            model
            for model in catalog_ids
            if "flash" in model and "flash-lite" not in model and "image" not in model
        )
        pro_models = tuple(model for model in catalog_ids if "pro" in model and "image" not in model)
        image_models = tuple(model for model in catalog_ids if "image" in model)

        return (
            GeminiModelFamily(
                family="gemini-flash-lite",
                catalog_patterns=("gemini-*-flash-lite", "models/gemini-*-flash-lite"),
                catalog_models=flash_lite_models,
                cost_posture="lowest_or_low",
                default_use="high-volume fast, routing, classification, OCR, and batch summary tasks",
                high_frequency_default_allowed=True,
                notes="Use the lowest capable Flash-Lite model before trying larger Gemini families.",
            ),
            GeminiModelFamily(
                family="gemini-flash",
                catalog_patterns=("gemini-*-flash", "models/gemini-*-flash"),
                catalog_models=flash_models,
                cost_posture="low_to_medium",
                default_use="balanced legal review, extraction retry, and structured drafting",
                high_frequency_default_allowed=False,
                notes="Use as the first quality step after Flash-Lite fails deterministic checks.",
            ),
            GeminiModelFamily(
                family="gemini-pro",
                catalog_patterns=("gemini-*-pro", "gemini-*-pro-preview"),
                catalog_models=pro_models,
                cost_posture="premium",
                default_use="operator-approved complex reasoning and final review exceptions",
                high_frequency_default_allowed=False,
                notes="Never make Pro or preview variants the default for high-volume tasks.",
            ),
            GeminiModelFamily(
                family="gemini-image",
                catalog_patterns=("gemini-*-image", "models/gemini-*-image"),
                catalog_models=image_models,
                cost_posture="media_priced",
                default_use="explicit media tasks only",
                high_frequency_default_allowed=False,
                notes="Image models are selected by media routes, not by text cheap-first defaults.",
            ),
        )

    def _prefix_compatibility(self) -> dict[str, Any]:
        return {
            "gateway": "NewAPI",
            "request_shape": "OpenAI-compatible chat completions model field",
            "openai_compatible": True,
            "accepted_prefix_examples": [
                {
                    "shape": "catalog id",
                    "example": "gemini-2.5-flash-lite",
                    "normalization": "direct catalog lookup",
                },
                {
                    "shape": "Google model path",
                    "example": "models/gemini-2.5-flash-lite",
                    "normalization": "strip models/ prefix for catalog checks",
                },
                {
                    "shape": "provider slash",
                    "example": "google/gemini-2.5-flash-lite",
                    "normalization": "strip provider prefix for catalog checks",
                },
                {
                    "shape": "provider colon",
                    "example": "google:gemini-2.5-flash-lite",
                    "normalization": "strip provider prefix for catalog checks",
                },
            ],
            "pass_through_rule": (
                "Gateway model ids that are not catalog-known may be passed explicitly, "
                "but they must not become high-frequency defaults until catalog review confirms tier and stability."
            ),
        }

    def _default_recommendations(self) -> tuple[TaskDefaultRecommendation, ...]:
        return (
            TaskDefaultRecommendation(
                task="fast",
                recommended_model="gemini-2.5-flash-lite",
                model_family="gemini-flash-lite",
                cost_tier="lowest",
                route_mode="cheap_first",
                high_frequency=True,
                escalation_after="schema failure, empty output, or low confidence",
                rationale="Fast preflight and routing are high-volume, so the default must be Flash-Lite.",
            ),
            TaskDefaultRecommendation(
                task="classification",
                recommended_model="gemini-2.5-flash-lite",
                model_family="gemini-flash-lite",
                cost_tier="lowest",
                route_mode="cheap_first",
                high_frequency=True,
                escalation_after="label ambiguity or required field mismatch",
                rationale="Classification should stay on the lowest capable Gemini family unless quality checks fail.",
            ),
            TaskDefaultRecommendation(
                task="ocr",
                recommended_model="gemini-2.5-flash-lite",
                model_family="gemini-flash-lite",
                cost_tier="lowest",
                route_mode="cheap_first",
                high_frequency=True,
                escalation_after="low text confidence, image-only pages, or extraction mismatch",
                rationale="OCR assist can run across many pages, so default cost must be minimized.",
            ),
            TaskDefaultRecommendation(
                task="review",
                recommended_model="gemini-2.5-flash",
                model_family="gemini-flash",
                cost_tier="low",
                route_mode="balanced_after_preflight",
                high_frequency=False,
                escalation_after="citation, evidence, or legal completeness gate failure",
                rationale="Legal review needs stronger reasoning than preflight but should avoid premium defaults.",
            ),
            TaskDefaultRecommendation(
                task="document_generation",
                recommended_model="gemini-2.5-flash",
                model_family="gemini-flash",
                cost_tier="low",
                route_mode="balanced_after_template_checks",
                high_frequency=False,
                escalation_after="template blocker, missing facts, or lawyer review request",
                rationale="Drafting should use template gates first, then balanced Flash for structured text.",
            ),
            TaskDefaultRecommendation(
                task="large_pdf_final_review",
                recommended_model="gemini-2.5-pro",
                model_family="gemini-pro",
                cost_tier="premium",
                route_mode="premium_exception",
                high_frequency=False,
                escalation_after="not applicable; this route already requires explicit exception handling",
                rationale="Large PDF and final review may need Pro, but this cannot bleed into high-volume defaults.",
            ),
        )

    def _cheap_first_task_ladder(self) -> list[dict[str, Any]]:
        return [
            {
                "task_group": "high_volume_preflight",
                "tasks": list(HIGH_FREQUENCY_TASKS),
                "ladder": [
                    {
                        "order": 1,
                        "model": "gemini-2.5-flash-lite",
                        "cost_tier": "lowest",
                        "role": "default",
                    },
                    {
                        "order": 2,
                        "model": "gemini-2.5-flash",
                        "cost_tier": "low",
                        "role": "quality retry",
                    },
                    {
                        "order": 3,
                        "model": "gemini-2.5-pro",
                        "cost_tier": "premium",
                        "role": "operator-approved exception only",
                    },
                ],
                "escalation_signals": [
                    "json_parse_error",
                    "missing_required_fields",
                    "citation_or_evidence_gate_failed",
                    "low_confidence",
                ],
                "stop_signals": ["privacy_high", "unsafe_instruction", "missing_user_material"],
            },
            {
                "task_group": "legal_review_and_generation",
                "tasks": ["review", "document_generation", "contract_analysis"],
                "ladder": [
                    {
                        "order": 1,
                        "model": "gemini-2.5-flash-lite",
                        "cost_tier": "lowest",
                        "role": "cheap precheck and issue extraction",
                    },
                    {
                        "order": 2,
                        "model": "gemini-2.5-flash",
                        "cost_tier": "low",
                        "role": "default drafting and review",
                    },
                    {
                        "order": 3,
                        "model": "gemini-2.5-pro",
                        "cost_tier": "premium",
                        "role": "final-review exception",
                    },
                ],
                "escalation_signals": [
                    "weak_citations",
                    "evidence_conflict",
                    "complex_legal_reasoning",
                    "lawyer_review_requested",
                ],
                "stop_signals": ["missing_facts", "delivery_blocked", "privacy_high"],
            },
        ]

    def _unknown_model_policy(self) -> dict[str, Any]:
        return {
            "gemini_like_detection": [
                "model id contains gemini after removing common gateway prefixes",
                "model id matches a known catalog id after slash or colon normalization",
            ],
            "catalog_review_status": "catalog_review",
            "warning_level": "warn",
            "default_allowed_for_high_frequency": False,
            "allowed_use": "explicit request only until catalog review confirms price, stability, and family",
            "required_review_fields": [
                "canonical_model_id",
                "provider_route",
                "family",
                "cost_tier",
                "stability",
                "high_frequency_default_allowed",
            ],
        }

    def _forbidden_default_rules(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "no_premium_or_preview_high_frequency_default",
                "applies_to_tasks": list(HIGH_FREQUENCY_TASKS),
                "blocked_model_markers": list(PREMIUM_DEFAULT_MARKERS),
                "blocked_cost_tiers": ["premium"],
                "action": "reject_default_and_warn",
                "allowed_as": "operator-approved escalation or final-review exception only",
            },
            {
                "id": "unknown_gemini_like_needs_catalog_review",
                "applies_to_tasks": list(HIGH_FREQUENCY_TASKS),
                "blocked_model_markers": ["unknown_gemini_like"],
                "blocked_cost_tiers": ["unverified"],
                "action": "warn_and_keep_explicit_only",
                "allowed_as": "manual experiment outside high-frequency defaults",
            },
        ]

    def _review_observed_model(self, observed: Any) -> ObservedModelReview:
        raw_model = self._model_id_from_observed(observed)
        normalized_model = canonical_model_id(raw_model)
        profile = model_profile(raw_model) if raw_model else None
        gemini_like = self._is_gemini_like(raw_model) or bool(profile and profile.family == "gemini")
        premium_like = self._is_premium_or_preview(raw_model) or bool(
            profile and (profile.cost_tier == "premium" or profile.status == "preview")
        )

        if profile:
            status = "catalog_known"
            severity = "info"
            action = "allow_catalog_route"
        elif gemini_like:
            status = "catalog_review"
            severity = "warn"
            action = "warn_allow_explicit_only"
        else:
            status = "external_model"
            severity = "info"
            action = "ignore_for_gemini_defaults"

        default_allowed = bool(profile and gemini_like and not premium_like and "flash-lite" in profile.id)
        warnings: list[str] = []
        if status == "catalog_review":
            warnings.append("Unknown Gemini-like model requires catalog review before default use.")
        if premium_like:
            warnings.append("Pro, preview, or premium models cannot be high-frequency defaults.")

        return ObservedModelReview(
            raw_model=raw_model,
            normalized_model=normalized_model or (profile.id if profile else None),
            is_gemini_like=gemini_like,
            status=status,
            severity=severity,
            action=action,
            default_allowed_for_high_frequency=default_allowed,
            warnings=tuple(warnings),
        )

    def _model_id_from_observed(self, observed: Any) -> str:
        if isinstance(observed, str):
            return observed.strip()
        if isinstance(observed, dict):
            for key in ("id", "model", "name"):
                value = observed.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return str(observed or "").strip()

    def _is_gemini_like(self, model_id: str) -> bool:
        value = (model_id or "").strip().lower()
        if not value:
            return False
        candidates = {value, value.rsplit("/", 1)[-1], value.rsplit(":", 1)[-1]}
        return any(candidate.startswith("gemini-") or "gemini-" in candidate for candidate in candidates)

    def _is_premium_or_preview(self, model_id: str) -> bool:
        value = (model_id or "").strip().lower()
        if not value:
            return False
        parts = [part for part in value.replace("/", "-").replace(":", "-").replace("_", "-").split("-") if part]
        return any(marker in parts for marker in PREMIUM_DEFAULT_MARKERS)
