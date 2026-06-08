from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services import model_catalog
from services.model_default_candidate_selector import ModelDefaultCandidateSelectorService
from services.model_catalog import ModelProfile


COST_RANK = {"lowest": 0, "low": 1, "medium": 2, "premium": 3}
LATENCY_RANK = {"fastest": 0, "fast": 1, "medium": 2, "slower": 3}


@dataclass(frozen=True)
class ModelTaskRequirement:
    task: str
    display_name: str
    required_capabilities: tuple[str, ...]
    preferred_capabilities: tuple[str, ...]
    max_cost_tier: str
    preferred_latency_tier: str
    default_alias: str
    reason: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_capabilities"] = list(self.required_capabilities)
        data["preferred_capabilities"] = list(self.preferred_capabilities)
        return data


class ModelCapabilityMatrixService:
    """Ranks Gemini models by capability fit, cost, and latency for each project task."""

    def __init__(
        self,
        candidate_selector: ModelDefaultCandidateSelectorService | None = None,
        catalog: tuple[ModelProfile, ...] | None = None,
    ) -> None:
        self.catalog = catalog or model_catalog.GEMINI_MODEL_CATALOG
        self.candidate_selector = candidate_selector or ModelDefaultCandidateSelectorService(catalog=self.catalog)

    def build_matrix(self) -> dict[str, Any]:
        tasks = [self._task_row(requirement) for requirement in self._requirements()]
        return {
            "status": "ready",
            "selection_policy": [
                "Filter out models missing required capabilities.",
                "Prefer stable models before preview models for defaults.",
                "Sort by cost tier, then latency tier, then capability fit.",
                "Keep premium models as explicit exceptions for PDF, complex reasoning, media, or operator-approved use.",
            ],
            "source_notes": [
                "Pricing fields are from Google Gemini API paid-tier documentation when available.",
                "Gateway names and billing may differ; unknown NewAPI model names are still passed through by the runtime router.",
                "The matrix never stores or returns API keys, prompts, documents, or user identifiers.",
            ],
            "tasks": tasks,
            "coverage": {
                "task_count": len(tasks),
                "catalog_model_count": len(self.catalog),
                "recommended_models": sorted({task["recommended_model"] for task in tasks if task["recommended_model"]}),
                "premium_exception_tasks": [
                    task["task"]
                    for task in tasks
                    if task["requirement"]["max_cost_tier"] == "premium"
                ],
            },
        }

    def recommend(self, task: str) -> dict[str, Any] | None:
        normalized = (task or "").strip().lower()
        for row in self.build_matrix()["tasks"]:
            if row["task"] == normalized:
                return row
        return None

    def _requirements(self) -> tuple[ModelTaskRequirement, ...]:
        return (
            ModelTaskRequirement(
                task="fast",
                display_name="Fast routing and light extraction",
                required_capabilities=("text", "json"),
                preferred_capabilities=("classification",),
                max_cost_tier="lowest",
                preferred_latency_tier="fastest",
                default_alias="auto-fast",
                reason="High-volume routing, preflight, and triage should use the cheapest JSON-capable text model.",
            ),
            ModelTaskRequirement(
                task="ocr",
                display_name="OCR and visual text extraction",
                required_capabilities=("vision", "ocr"),
                preferred_capabilities=("json", "classification"),
                max_cost_tier="lowest",
                preferred_latency_tier="fastest",
                default_alias="auto-ocr",
                reason="OCR can run across many pages; default to the cheapest vision-capable model.",
            ),
            ModelTaskRequirement(
                task="classification",
                display_name="Material classification",
                required_capabilities=("text", "json", "classification"),
                preferred_capabilities=("ocr",),
                max_cost_tier="lowest",
                preferred_latency_tier="fastest",
                default_alias="auto-fast",
                reason="Document and evidence classification is high-volume and should stay on the cheapest structured model.",
            ),
            ModelTaskRequirement(
                task="review",
                display_name="Balanced legal review",
                required_capabilities=("text", "json", "review"),
                preferred_capabilities=("vision",),
                max_cost_tier="low",
                preferred_latency_tier="fast",
                default_alias="auto-review",
                reason="Legal analysis needs stronger reasoning than triage but should avoid premium defaults.",
            ),
            ModelTaskRequirement(
                task="pdf",
                display_name="Large PDF and final review",
                required_capabilities=("text", "long-context", "complex-reasoning"),
                preferred_capabilities=("vision", "json"),
                max_cost_tier="premium",
                preferred_latency_tier="slower",
                default_alias="auto-pdf",
                reason="Long documents and hard legal reasoning can justify premium exception routing.",
            ),
            ModelTaskRequirement(
                task="grounded-research",
                display_name="Grounded legal research",
                required_capabilities=("text", "grounding"),
                preferred_capabilities=("json", "complex-reasoning"),
                max_cost_tier="low",
                preferred_latency_tier="fast",
                default_alias="auto-grounded-research",
                reason="Legal RAG and source lookup need grounding support before premium reasoning is considered.",
            ),
            ModelTaskRequirement(
                task="agentic",
                display_name="Agentic workflow planning",
                required_capabilities=("text", "agentic"),
                preferred_capabilities=("json", "grounding"),
                max_cost_tier="low",
                preferred_latency_tier="fast",
                default_alias="auto-agentic",
                reason="Agentic planning should start with low-cost Gemini 3 Flash-Lite style models.",
            ),
            ModelTaskRequirement(
                task="image",
                display_name="Image generation and editing",
                required_capabilities=("image",),
                preferred_capabilities=("image-edit",),
                max_cost_tier="premium",
                preferred_latency_tier="medium",
                default_alias="explicit",
                reason="Image models are media-specific and should be selected explicitly.",
            ),
            ModelTaskRequirement(
                task="embedding",
                display_name="Embedding and legal RAG indexing",
                required_capabilities=("embedding", "text"),
                preferred_capabilities=("batch",),
                max_cost_tier="lowest",
                preferred_latency_tier="fast",
                default_alias="auto-embedding",
                reason="Legal source indexes and deduping are high-volume, so text embeddings should start on the cheapest stable embedding model.",
            ),
        )

    def _task_row(self, requirement: ModelTaskRequirement) -> dict[str, Any]:
        candidates = [
            self._candidate(profile, requirement)
            for profile in self.catalog
            if _has_required(profile, requirement.required_capabilities)
            and _task_family_allowed(profile, requirement)
        ]
        candidates.sort(key=lambda item: item["sort_key"])
        for item in candidates:
            item.pop("sort_key", None)
        candidate_fallback = candidates[0]["model_id"] if candidates else model_catalog.task_default_model(requirement.task)
        recommended = self.candidate_selector.recommended_model_for_task(
            requirement.task,
            fallback=candidate_fallback,
        )

        return {
            "task": requirement.task,
            "requirement": requirement.to_api(),
            "recommended_model": recommended,
            "runtime_default_model": model_catalog.task_default_model(requirement.task),
            "runtime_default_is_recommended": model_catalog.task_default_model(requirement.task) == recommended,
            "candidate_count": len(candidates),
            "candidates": candidates,
        }

    def _candidate(self, profile: ModelProfile, requirement: ModelTaskRequirement) -> dict[str, Any]:
        preferred_hits = [cap for cap in requirement.preferred_capabilities if cap in profile.capabilities]
        missing_preferred = [cap for cap in requirement.preferred_capabilities if cap not in profile.capabilities]
        over_budget = COST_RANK.get(profile.cost_tier, 99) > COST_RANK.get(requirement.max_cost_tier, 99)
        preview_penalty = 1 if profile.status != "stable" else 0
        fit_score = max(0, 100 - len(missing_preferred) * 10 - (15 if over_budget else 0) - preview_penalty * 5)
        return {
            "model_id": profile.id,
            "status": profile.status,
            "cost_tier": profile.cost_tier,
            "latency_tier": profile.latency_tier,
            "context_window_tokens": profile.context_window_tokens,
            "input_usd_per_million_tokens": profile.input_usd_per_million_tokens,
            "output_usd_per_million_tokens": profile.output_usd_per_million_tokens,
            "preferred_capability_hits": preferred_hits,
            "missing_preferred_capabilities": missing_preferred,
            "over_task_budget": over_budget,
            "fit_score": fit_score,
            "sort_key": (
                1 if over_budget else 0,
                preview_penalty,
                COST_RANK.get(profile.cost_tier, 99),
                LATENCY_RANK.get(profile.latency_tier, 99),
                -fit_score,
                profile.id,
            ),
        }


def _has_required(profile: ModelProfile, required_capabilities: tuple[str, ...]) -> bool:
    return all(capability in profile.capabilities for capability in required_capabilities)


def _task_family_allowed(profile: ModelProfile, requirement: ModelTaskRequirement) -> bool:
    is_embedding_model = "embedding" in set(profile.capabilities) or "embedding" in profile.id
    return requirement.task == "embedding" if is_embedding_model else requirement.task != "embedding"
