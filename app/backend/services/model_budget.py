"""
Budget policy helpers for model routing.

This module explains the routing decision. It does not store prompts or secrets,
and it does not block calls by itself; callers can use the policy fields to warn,
confirm, or enforce stricter behavior later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.config import settings
from services.model_catalog import model_profile, resolve_model, task_default_model


TASK_GROUPS: dict[str, dict[str, Any]] = {
    "fast": {
        "budget_mode": "cheap-first",
        "max_cost_tier": "lowest",
        "reason": "High-volume routing, OCR, classification, and triage should use the cheapest capable model.",
    },
    "ocr": {
        "budget_mode": "cheap-first",
        "max_cost_tier": "lowest",
        "reason": "OCR fallback can run on many scanned pages, so it should default to Flash-Lite.",
    },
    "classification": {
        "budget_mode": "cheap-first",
        "max_cost_tier": "lowest",
        "reason": "Material classification is high-volume and low-risk after deterministic rules.",
    },
    "review": {
        "budget_mode": "balanced",
        "max_cost_tier": "low",
        "reason": "Legal review needs better reasoning than triage but should still avoid premium defaults.",
    },
    "grounded-research": {
        "budget_mode": "cheap-first-grounded",
        "max_cost_tier": "low",
        "reason": "Grounded legal research should start on the cheapest Gemini model with grounding capability before escalating.",
    },
    "agentic": {
        "budget_mode": "cheap-first-agentic",
        "max_cost_tier": "low",
        "reason": "Agentic workflow planning should start on a low-cost Gemini model with agentic capability.",
    },
    "pdf": {
        "budget_mode": "premium-exception",
        "max_cost_tier": "premium",
        "reason": "Large PDFs and complex final reviews may need premium context and reasoning.",
    },
    "image": {
        "budget_mode": "explicit-media",
        "max_cost_tier": "premium",
        "reason": "Media generation models are selected explicitly and priced differently from text tokens.",
    },
    "video": {
        "budget_mode": "explicit-video-media",
        "max_cost_tier": "premium",
        "reason": "Video generation routes through explicit media defaults; provider pricing and duration units must be reviewed separately.",
    },
    "audio": {
        "budget_mode": "explicit-speech-media",
        "max_cost_tier": "premium",
        "reason": "Speech generation routes through explicit speech defaults; voice and audio billing units must be reviewed separately.",
    },
    "transcription": {
        "budget_mode": "explicit-transcription",
        "max_cost_tier": "premium",
        "reason": "Speech-to-text routes through explicit transcription defaults; audio duration billing must be reviewed separately.",
    },
}

COST_TIER_RANK = {"lowest": 0, "low": 1, "medium": 2, "premium": 3}


@dataclass(frozen=True)
class ModelBudgetDecision:
    task: str
    requested_model: str | None
    resolved_model: str
    budget_mode: str
    cost_tier: str | None
    max_cost_tier: str
    is_known_model: bool
    is_over_budget: bool
    requires_operator_review: bool
    recommended_model: str
    reason: str

    def to_api(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "requested_model": self.requested_model,
            "resolved_model": self.resolved_model,
            "budget_mode": self.budget_mode,
            "cost_tier": self.cost_tier,
            "max_cost_tier": self.max_cost_tier,
            "is_known_model": self.is_known_model,
            "is_over_budget": self.is_over_budget,
            "requires_operator_review": self.requires_operator_review,
            "recommended_model": self.recommended_model,
            "reason": self.reason,
        }


def normalize_budget_task(task: str | None) -> str:
    value = (task or "fast").strip().lower()
    if value in {"cheap", "routing"}:
        return "fast"
    if value in {"classifier"}:
        return "classification"
    if value in {"legal-review", "analysis", "chat", "document-generation"}:
        return "review"
    if value in {"large-pdf", "final-review", "complex"}:
        return "pdf"
    if value in {"genimg", "visual", "image-edit"}:
        return "image"
    if value in {"genvideo", "visual-video", "image-to-video"}:
        return "video"
    if value in {"tts", "speech", "speech-generation"}:
        return "audio"
    if value in {"transcribe", "speech-to-text", "stt"}:
        return "transcription"
    if value in {"grounded_research", "research", "rag-research"}:
        return "grounded-research"
    if value in {"agentic-routing", "workflow-planning"}:
        return "agentic"
    return value if value in TASK_GROUPS else "review"


def model_budget_decision(model: str | None = None, *, task: str = "fast") -> ModelBudgetDecision:
    normalized_task = normalize_budget_task(task)
    policy = TASK_GROUPS[normalized_task]
    resolved_model = resolve_model(model, task=normalized_task)
    recommended_model = task_default_model(normalized_task)
    profile = model_profile(resolved_model)
    cost_tier = profile.cost_tier if profile else None
    max_cost_tier = str(policy["max_cost_tier"])
    is_known_model = profile is not None
    is_over_budget = _is_over_budget(cost_tier=cost_tier, max_cost_tier=max_cost_tier)
    premium_requires_review = bool(getattr(settings, "app_ai_premium_requires_review", True))
    requires_operator_review = (
        premium_requires_review
        and cost_tier == "premium"
        and normalized_task not in {"pdf", "image", "video", "audio", "transcription"}
    )

    reason = str(policy["reason"])
    if is_over_budget:
        reason += " Requested model is above the task budget; use the recommended model unless an operator approves."
    elif not is_known_model:
        reason += " Model is not in the local catalog; route is allowed but pricing and tier are unverified."

    return ModelBudgetDecision(
        task=normalized_task,
        requested_model=(model or None),
        resolved_model=resolved_model,
        budget_mode=str(policy["budget_mode"]),
        cost_tier=cost_tier,
        max_cost_tier=max_cost_tier,
        is_known_model=is_known_model,
        is_over_budget=is_over_budget,
        requires_operator_review=requires_operator_review,
        recommended_model=recommended_model,
        reason=reason,
    )


def budget_policy_for_api() -> dict[str, Any]:
    decisions = [
        model_budget_decision(None, task=task).to_api()
        for task in (
            "fast",
            "ocr",
            "classification",
            "review",
            "grounded-research",
            "agentic",
            "pdf",
            "image",
            "video",
            "audio",
            "transcription",
        )
    ]
    return {
        "premium_requires_review": bool(getattr(settings, "app_ai_premium_requires_review", True)),
        "cost_tier_rank": COST_TIER_RANK,
        "task_decisions": decisions,
    }


def _is_over_budget(*, cost_tier: str | None, max_cost_tier: str) -> bool:
    if cost_tier is None:
        return False
    return COST_TIER_RANK.get(cost_tier, 99) > COST_TIER_RANK.get(max_cost_tier, 99)
