from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from services import model_catalog
from services.gemini_newapi_cheap_first_policy import GeminiNewapiCheapFirstPolicyService
from services.gemini_newapi_observed_model_extraction import extract_observed_model_ids, safe_model_id
from services.model_default_candidate_selector import ModelDefaultCandidateSelectorService
from services.model_catalog import (
    canonical_model_id,
    model_profile,
    resolve_model,
    task_default_model,
)


HIGH_FREQUENCY_TASKS = {"cheap", "fast", "routing", "triage", "classification", "classifier", "ocr", "batch_summary"}
BALANCED_TASKS = {"review", "legal-review", "analysis", "chat", "document-generation", "contract_analysis"}
PREMIUM_EXCEPTION_TASKS = {"pdf", "large-pdf", "large_pdf", "final-review", "final_review", "complex"}
SENSITIVE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|token)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TaskRecommendation:
    task: str
    selected_model: str
    canonical_model: str | None
    cost_tier: str
    route_mode: str
    decision: str
    high_frequency: bool
    premium_exception: bool
    escalation_chain: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["escalation_chain"] = list(self.escalation_chain)
        data["warnings"] = list(self.warnings)
        return data


@dataclass(frozen=True)
class ObservedModelReview:
    raw_model: str
    canonical_model: str | None
    status: str
    action: str
    cost_tier: str | None
    default_allowed_for_high_frequency: bool
    warnings: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["warnings"] = list(self.warnings)
        return data


class GeminiNewapiModelSelectorService:
    """Normalize Gemini/NewAPI model ids and produce cheap-first task choices."""

    def __init__(
        self,
        policy_service: GeminiNewapiCheapFirstPolicyService | None = None,
        candidate_selector: ModelDefaultCandidateSelectorService | None = None,
    ) -> None:
        self.policy_service = policy_service or GeminiNewapiCheapFirstPolicyService()
        self.candidate_selector = candidate_selector or ModelDefaultCandidateSelectorService()

    def build_selector(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        tasks = self._tasks(data.get("tasks"))
        explicit_models = data.get("explicit_models") if isinstance(data.get("explicit_models"), dict) else {}
        observed_model_extraction = extract_observed_model_ids(data)
        observed_models = observed_model_extraction["observed_models"]
        recommendations = [self._recommendation(task, explicit_models.get(task)) for task in tasks]
        observed_reviews = [self._observed_review(item).to_api() for item in observed_models]
        policy = self.policy_service.build_policy(observed_models=observed_models)
        recommendation_payloads = [item.to_api() for item in recommendations]
        catalog_reviews = [item for item in observed_reviews if item["status"] == "catalog_review"]
        unknown_models = [item for item in observed_reviews if item["status"] in {"catalog_review", "external_model"}]

        return {
            "status": "needs_catalog_review" if catalog_reviews else "ready",
            "summary": {
                "task_count": len(tasks),
                "recommendation_count": len(recommendations),
                "cheap_first_ready_count": sum(1 for item in recommendation_payloads if item["decision"] == "cheap_first_ready"),
                "balanced_route_count": sum(1 for item in recommendation_payloads if item["decision"] == "balanced_after_precheck"),
                "premium_exception_count": sum(1 for item in recommendation_payloads if item["premium_exception"] is True),
                "catalog_review_count": len(catalog_reviews),
                "unknown_model_count": len(unknown_models),
                "observed_model_candidate_count": observed_model_extraction["summary"]["candidate_count"],
                "accepted_observed_model_count": observed_model_extraction["summary"]["accepted_model_count"],
                "dropped_observed_model_count": observed_model_extraction["summary"]["dropped_model_count"],
                "observed_model_source_count": len(observed_model_extraction["summary"]["source_fields"]),
                "known_catalog_model_count": len(model_catalog.GEMINI_MODEL_CATALOG),
                "raw_payload_echoed": False,
            },
            "source_summaries": {
                "observed_model_extraction": observed_model_extraction["summary"],
            },
            "task_recommendations": recommendation_payloads,
            "observed_model_reviews": observed_reviews,
            "cheap_first_ladders": policy["cheap_first_task_ladder"],
            "normalization_rules": {
                "accepted_shapes": [
                    "gemini-2.5-flash-lite",
                    "models/gemini-2.5-flash-lite",
                    "google/gemini-2.5-flash-lite",
                    "google:gemini-2.5-flash-lite",
                ],
                "unknown_gemini_like_policy": "warn_allow_explicit_only_until_catalog_review",
                "high_frequency_default_rule": "Flash-Lite catalog models first; Pro, preview, and unknown Gemini-like ids are not high-frequency defaults.",
            },
            "privacy_boundary": {
                "raw_payload_echoed": False,
                "credentials_included": False,
                "credential_material_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "emails_included": False,
                "output_scope": "metadata-only model ids, canonical ids, task labels, cost tiers, warnings, and cheap-first candidate chains",
            },
            "validation_commands": [
                "python -m pytest tests/test_gemini_newapi_model_selector.py -q",
                "python -m pytest tests/test_gemini_newapi_cheap_first_policy.py tests/test_model_catalog.py -q",
                "npm run typecheck",
                "npm run build",
            ],
        }

    def _recommendation(self, task: str, explicit_model: Any = None) -> TaskRecommendation:
        normalized_task = self._task_token(task)
        requested_model = self._safe_model_id(explicit_model)
        selected_model = resolve_model(requested_model, task=normalized_task) if requested_model else task_default_model(normalized_task)
        canonical = canonical_model_id(selected_model)
        profile = model_profile(selected_model) if selected_model else None
        cost_tier = profile.cost_tier if profile else "unverified"
        high_frequency = normalized_task in HIGH_FREQUENCY_TASKS
        premium_exception = normalized_task in PREMIUM_EXCEPTION_TASKS or cost_tier == "premium"
        warnings: list[str] = []

        if high_frequency and (premium_exception or not canonical or "flash-lite" not in (canonical or "")):
            warnings.append("High-frequency tasks must stay on catalog-known Flash-Lite defaults unless an operator approves escalation.")
        if not canonical and selected_model:
            warnings.append("Model id is not in the local catalog; keep explicit-only until price and stability review.")

        if premium_exception:
            decision = "premium_exception_required"
            route_mode = "operator_approved_exception"
        elif normalized_task in BALANCED_TASKS:
            decision = "balanced_after_precheck"
            route_mode = "cheap_precheck_then_balanced"
        elif warnings:
            decision = "catalog_review_required"
            route_mode = "explicit_only"
        else:
            decision = "cheap_first_ready"
            route_mode = "cheap_first"

        return TaskRecommendation(
            task=normalized_task,
            selected_model=selected_model,
            canonical_model=canonical,
            cost_tier=cost_tier,
            route_mode=route_mode,
            decision=decision,
            high_frequency=high_frequency,
            premium_exception=premium_exception,
            escalation_chain=tuple(self._escalation_chain(normalized_task)),
            warnings=tuple(warnings),
        )

    def _observed_review(self, raw: Any) -> ObservedModelReview:
        raw_model = self._safe_model_id(raw)
        canonical = canonical_model_id(raw_model)
        profile = model_profile(raw_model) if raw_model else None
        gemini_like = self._is_gemini_like(raw_model)
        warnings: list[str] = []
        if profile:
            status = "catalog_known"
            action = "allow_catalog_route"
            default_allowed = "flash-lite" in profile.id and profile.cost_tier in {"lowest", "low"} and profile.status == "stable"
        elif gemini_like:
            status = "catalog_review"
            action = "warn_allow_explicit_only"
            default_allowed = False
            warnings.append("Unknown Gemini-like model requires catalog review before default use.")
        else:
            status = "external_model"
            action = "ignore_for_gemini_defaults"
            default_allowed = False
            warnings.append("External non-Gemini model is outside Gemini cheap-first defaults.")

        if profile and (profile.cost_tier == "premium" or profile.status == "preview"):
            warnings.append("Premium or preview models require explicit exception handling.")
            default_allowed = False

        return ObservedModelReview(
            raw_model=raw_model,
            canonical_model=canonical,
            status=status,
            action=action,
            cost_tier=profile.cost_tier if profile else None,
            default_allowed_for_high_frequency=default_allowed,
            warnings=tuple(warnings),
        )

    def _tasks(self, raw_tasks: Any) -> list[str]:
        default_tasks = ["fast", "routing", "classification", "ocr", "review", "document-generation", "large-pdf"]
        if not isinstance(raw_tasks, list):
            return default_tasks
        tasks = []
        for item in raw_tasks[:20]:
            task = self._task_token(item)
            if task and task not in tasks:
                tasks.append(task)
        return tasks or default_tasks

    def _task_token(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace("_", "-")[:64]
        if not raw or SENSITIVE_PATTERN.search(raw):
            return ""
        return re.sub(r"[^a-z0-9:-]+", "-", raw).strip("-") or "fast"

    def _safe_model_id(self, value: Any) -> str:
        return safe_model_id(value)

    def _is_gemini_like(self, model_id: str) -> bool:
        value = (model_id or "").strip().lower()
        candidates = {value, value.rsplit("/", 1)[-1], value.rsplit(":", 1)[-1]}
        return any(candidate.startswith("gemini-") or "gemini-" in candidate for candidate in candidates)

    def _escalation_chain(self, task: str) -> list[str]:
        ladder = self.candidate_selector.default_ladder_for_task(task)
        chain = [str(item["model"]) for item in ladder if item.get("model")]
        if chain:
            return chain
        if task in PREMIUM_EXCEPTION_TASKS:
            return ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"]
        if task in BALANCED_TASKS:
            return ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"]
        return ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
