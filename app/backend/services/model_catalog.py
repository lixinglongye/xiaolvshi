"""
Model catalog and routing policy for OpenAI-compatible AI gateways.

The app can run through NewAPI, Gemini's OpenAI-compatible endpoint, or any
other gateway that accepts OpenAI SDK chat completion requests. This module
keeps model selection explicit, cost-aware, and free of API keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.config import settings


@dataclass(frozen=True)
class ModelProfile:
    id: str
    provider: str
    family: str
    cost_tier: str
    latency_tier: str
    capabilities: tuple[str, ...]
    best_for: tuple[str, ...]
    notes: str = ""


GEMINI_MODEL_CATALOG: tuple[ModelProfile, ...] = (
    ModelProfile(
        id="gemini-2.5-flash-lite",
        provider="google",
        family="gemini",
        cost_tier="lowest",
        latency_tier="fastest",
        capabilities=("text", "vision", "json", "ocr", "classification"),
        best_for=("routing", "ocr", "triage", "summaries", "cheap-batch-review"),
        notes="Default cost-first model for high-volume pipeline stages.",
    ),
    ModelProfile(
        id="gemini-2.5-flash",
        provider="google",
        family="gemini",
        cost_tier="low",
        latency_tier="fast",
        capabilities=("text", "vision", "json", "ocr", "review"),
        best_for=("legal-review", "document-analysis", "structured-extraction"),
        notes="Balanced default for legal analysis when quality matters.",
    ),
    ModelProfile(
        id="gemini-2.5-pro",
        provider="google",
        family="gemini",
        cost_tier="premium",
        latency_tier="slower",
        capabilities=("text", "vision", "json", "long-context", "complex-reasoning"),
        best_for=("final-review", "large-pdf", "hard-legal-reasoning"),
        notes="Use only for complex or failed stages unless explicitly selected.",
    ),
    ModelProfile(
        id="gemini-3.1-flash-lite",
        provider="google",
        family="gemini",
        cost_tier="low",
        latency_tier="fast",
        capabilities=("text", "vision", "json", "audio", "video", "agentic"),
        best_for=("agentic-routing", "translation", "simple-data-processing", "high-volume-tasks"),
        notes="Newer cost-efficient option; enable by setting APP_AI_CHEAP_MODEL when your gateway supports it.",
    ),
    ModelProfile(
        id="gemini-3.5-flash",
        provider="google",
        family="gemini",
        cost_tier="medium",
        latency_tier="fast",
        capabilities=("text", "vision", "json", "grounding", "coding", "agentic"),
        best_for=("agentic-workflows", "coding", "grounded-research", "sustained-reasoning"),
        notes="Current stable Flash option; more capable but more expensive than Flash-Lite defaults.",
    ),
    ModelProfile(
        id="gemini-2.5-flash-image",
        provider="google",
        family="gemini",
        cost_tier="low",
        latency_tier="medium",
        capabilities=("image", "image-edit"),
        best_for=("image-generation", "visual-evidence-illustration"),
    ),
    ModelProfile(
        id="gemini-3-pro-image",
        provider="google",
        family="gemini",
        cost_tier="premium",
        latency_tier="slower",
        capabilities=("image", "image-edit"),
        best_for=("high-quality-image-generation",),
    ),
)


def _catalog_by_id() -> dict[str, ModelProfile]:
    return {item.id: item for item in GEMINI_MODEL_CATALOG}


def _configured_model(name: str | None, fallback: str) -> str:
    if name and name.strip():
        return name.strip()
    return fallback


def cheap_text_model() -> str:
    return _configured_model(getattr(settings, "app_ai_cheap_model", None), "gemini-2.5-flash-lite")


def balanced_text_model() -> str:
    return _configured_model(getattr(settings, "app_ai_balanced_model", None), "gemini-2.5-flash")


def premium_text_model() -> str:
    return _configured_model(getattr(settings, "app_ai_premium_model", None), "gemini-2.5-pro")


def task_default_model(task: str) -> str:
    """Return the configured model for a known task, preferring low-cost defaults."""
    task = (task or "fast").strip().lower()
    if task in {"fast", "cheap", "routing", "classification", "classifier", "ocr"}:
        return cheap_text_model()
    if task in {"review", "legal-review", "analysis", "chat", "document-generation"}:
        return _configured_model(getattr(settings, "app_ai_review_model", None), balanced_text_model())
    if task in {"pdf", "large-pdf", "final-review", "complex"}:
        return _configured_model(getattr(settings, "app_ai_pdf_model", None), premium_text_model())
    return balanced_text_model()


def resolve_model(model: str | None, *, task: str = "fast") -> str:
    """
    Resolve request model names and stable aliases.

    Explicit gateway model names are passed through unchanged so NewAPI can expose
    new Gemini models without a backend release. Aliases keep callers stable.
    """
    value = (model or "").strip()
    if not value:
        return task_default_model(task)

    aliases = {
        "auto": task_default_model(task),
        "auto-fast": task_default_model("fast"),
        "auto-cheap": task_default_model("cheap"),
        "auto-ocr": task_default_model("ocr"),
        "auto-review": task_default_model("review"),
        "auto-pdf": task_default_model("pdf"),
        "cheap": cheap_text_model(),
        "balanced": balanced_text_model(),
        "premium": premium_text_model(),
    }
    return aliases.get(value.lower(), value)


def model_profile(model_id: str) -> ModelProfile | None:
    return _catalog_by_id().get(model_id)


def catalog_for_api() -> list[dict[str, object]]:
    configured = {
        "cheap": cheap_text_model(),
        "balanced": balanced_text_model(),
        "premium": premium_text_model(),
        "fast": task_default_model("fast"),
        "ocr": task_default_model("ocr"),
        "review": task_default_model("review"),
        "pdf": task_default_model("pdf"),
    }
    return [
        {
            "id": item.id,
            "provider": item.provider,
            "family": item.family,
            "cost_tier": item.cost_tier,
            "latency_tier": item.latency_tier,
            "capabilities": list(item.capabilities),
            "best_for": list(item.best_for),
            "notes": item.notes,
            "configured_roles": [role for role, model_id in configured.items() if model_id == item.id],
        }
        for item in GEMINI_MODEL_CATALOG
    ]


def allowed_model_hint(models: Iterable[str] | None = None) -> str:
    known = ", ".join(models or [item.id for item in GEMINI_MODEL_CATALOG])
    return f"Known Gemini models: {known}. Gateway-specific model names are also accepted."
