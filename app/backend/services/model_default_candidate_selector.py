from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services import model_catalog
from services.model_catalog import ModelProfile


COST_RANK = {"lowest": 0, "low": 1, "medium": 2, "premium": 3}
LATENCY_RANK = {"fastest": 0, "fast": 1, "medium": 2, "slower": 3}
TEXT_PRICE_MISSING_PENALTY = 999_999.0


@dataclass(frozen=True)
class TaskCandidatePolicy:
    task: str
    required_capabilities: tuple[str, ...]
    preferred_capabilities: tuple[str, ...]
    max_default_cost_tier: str
    fallback_model: str
    route_mode: str
    high_frequency: bool
    price_mode: str = "text"

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_capabilities"] = list(self.required_capabilities)
        data["preferred_capabilities"] = list(self.preferred_capabilities)
        return data


TASK_ALIASES = {
    "routing": "fast",
    "triage": "fast",
    "batch-summary": "fast",
    "batch_summary": "fast",
    "quote-extraction": "fast",
    "quote_extraction": "fast",
    "classifier": "classification",
    "legal-review": "review",
    "analysis": "review",
    "chat": "review",
    "contract-analysis": "review",
    "contract_analysis": "review",
    "document-generation": "document-generation",
    "document_generation": "document-generation",
    "large-pdf": "pdf",
    "large_pdf": "pdf",
    "final-review": "pdf",
    "final_review": "pdf",
    "complex": "pdf",
    "grounded_research": "grounded-research",
    "rag-research": "grounded-research",
    "workflow-planning": "agentic",
    "image-edit": "image",
    "genimg": "image",
    "visual": "image",
}


TASK_POLICIES: dict[str, TaskCandidatePolicy] = {
    "cheap": TaskCandidatePolicy(
        task="cheap",
        required_capabilities=("text", "json"),
        preferred_capabilities=("classification",),
        max_default_cost_tier="lowest",
        fallback_model="gemini-2.5-flash-lite",
        route_mode="cheap_first",
        high_frequency=True,
    ),
    "fast": TaskCandidatePolicy(
        task="fast",
        required_capabilities=("text", "json"),
        preferred_capabilities=("classification",),
        max_default_cost_tier="lowest",
        fallback_model="gemini-2.5-flash-lite",
        route_mode="cheap_first",
        high_frequency=True,
    ),
    "classification": TaskCandidatePolicy(
        task="classification",
        required_capabilities=("text", "json", "classification"),
        preferred_capabilities=("ocr",),
        max_default_cost_tier="lowest",
        fallback_model="gemini-2.5-flash-lite",
        route_mode="cheap_first",
        high_frequency=True,
    ),
    "ocr": TaskCandidatePolicy(
        task="ocr",
        required_capabilities=("vision", "ocr"),
        preferred_capabilities=("json", "classification"),
        max_default_cost_tier="lowest",
        fallback_model="gemini-2.5-flash-lite",
        route_mode="cheap_first",
        high_frequency=True,
    ),
    "review": TaskCandidatePolicy(
        task="review",
        required_capabilities=("text", "json", "review"),
        preferred_capabilities=("vision",),
        max_default_cost_tier="low",
        fallback_model="gemini-2.5-flash",
        route_mode="balanced_after_precheck",
        high_frequency=False,
    ),
    "document-generation": TaskCandidatePolicy(
        task="document-generation",
        required_capabilities=("text", "json", "review"),
        preferred_capabilities=("vision",),
        max_default_cost_tier="low",
        fallback_model="gemini-2.5-flash",
        route_mode="balanced_after_template_checks",
        high_frequency=False,
    ),
    "pdf": TaskCandidatePolicy(
        task="pdf",
        required_capabilities=("text", "long-context", "complex-reasoning"),
        preferred_capabilities=("vision", "json"),
        max_default_cost_tier="premium",
        fallback_model="gemini-2.5-pro",
        route_mode="premium_exception",
        high_frequency=False,
    ),
    "grounded-research": TaskCandidatePolicy(
        task="grounded-research",
        required_capabilities=("text", "grounding"),
        preferred_capabilities=("json", "agentic"),
        max_default_cost_tier="low",
        fallback_model="gemini-3.1-flash-lite",
        route_mode="grounded_cheap_first",
        high_frequency=False,
    ),
    "agentic": TaskCandidatePolicy(
        task="agentic",
        required_capabilities=("text", "agentic"),
        preferred_capabilities=("json", "grounding"),
        max_default_cost_tier="low",
        fallback_model="gemini-3.1-flash-lite",
        route_mode="agentic_cheap_first",
        high_frequency=False,
    ),
    "image": TaskCandidatePolicy(
        task="image",
        required_capabilities=("image",),
        preferred_capabilities=("image-edit",),
        max_default_cost_tier="low",
        fallback_model="gemini-2.5-flash-image",
        route_mode="media_explicit",
        high_frequency=False,
        price_mode="image",
    ),
}


class ModelDefaultCandidateSelectorService:
    """Select cheapest capable Gemini defaults from the local catalog metadata only."""

    def recommendation(self, task: str) -> dict[str, Any]:
        policy = self.policy_for_task(task)
        candidates = self.candidates_for_task(task)
        eligible = [item for item in candidates if item["default_eligible"]]
        selected = eligible[0]["model_id"] if eligible else policy.fallback_model
        selected_row = next((item for item in candidates if item["model_id"] == selected), None)
        return {
            "task": policy.task,
            "selected_model": selected,
            "selected_family": _family_label(selected),
            "selected_cost_tier": selected_row["cost_tier"] if selected_row else "unknown",
            "selected_latency_tier": selected_row["latency_tier"] if selected_row else "unknown",
            "route_mode": policy.route_mode,
            "high_frequency": policy.high_frequency,
            "fallback_model": policy.fallback_model,
            "candidate_count": len(candidates),
            "eligible_candidate_count": len(eligible),
            "policy": policy.to_api(),
            "candidates": candidates,
            "privacy_boundary": self._privacy_boundary(),
        }

    def recommended_model_for_task(self, task: str, *, fallback: str | None = None) -> str:
        recommendation = self.recommendation(task)
        selected = str(recommendation.get("selected_model") or "")
        return selected or fallback or self.policy_for_task(task).fallback_model

    def default_ladder_for_task(self, task: str, *, limit: int = 5) -> list[dict[str, Any]]:
        policy = self.policy_for_task(task)
        candidates = self.candidates_for_task(task)
        if not candidates:
            return [
                {
                    "order": 1,
                    "model": policy.fallback_model,
                    "cost_tier": "unknown",
                    "role": "configured fallback",
                    "default_eligible": False,
                    "pricing_status": "unknown",
                }
            ]

        ladder: list[dict[str, Any]] = []
        for candidate in candidates[: max(1, limit)]:
            ladder.append(
                {
                    "order": len(ladder) + 1,
                    "model": candidate["model_id"],
                    "cost_tier": candidate["cost_tier"],
                    "role": self._ladder_role(candidate, policy),
                    "default_eligible": candidate["default_eligible"],
                    "pricing_status": candidate["pricing_status"],
                    "catalog_status": candidate["catalog_status"],
                }
            )
        return ladder

    def candidates_for_task(self, task: str) -> list[dict[str, Any]]:
        policy = self.policy_for_task(task)
        rows = [
            self._candidate_row(profile, policy)
            for profile in model_catalog.GEMINI_MODEL_CATALOG
            if _has_required_capabilities(profile, policy.required_capabilities)
        ]
        rows.sort(key=lambda item: item["sort_key"])
        for row in rows:
            row.pop("sort_key", None)
        return rows

    def policy_for_task(self, task: str) -> TaskCandidatePolicy:
        normalized = normalize_task(task)
        return TASK_POLICIES.get(normalized, TASK_POLICIES["review"])

    def build_selector(self) -> dict[str, Any]:
        rows = [self.recommendation(task) for task in TASK_POLICIES]
        return {
            "id": "model-default-candidate-selector",
            "status": "ready",
            "summary": {
                "task_count": len(rows),
                "catalog_model_count": len(model_catalog.GEMINI_MODEL_CATALOG),
                "high_frequency_task_count": sum(1 for row in rows if row["high_frequency"]),
                "candidate_model_count": len(
                    {
                        candidate["model_id"]
                        for row in rows
                        for candidate in row["candidates"]
                    }
                ),
                "metadata_only": True,
                "gateway_called": False,
                "configuration_written": False,
            },
            "recommendations": rows,
            "privacy_boundary": self._privacy_boundary(),
            "validation_commands": [
                "python -m pytest tests/test_model_default_candidate_selector.py -q",
                "python -m pytest tests/test_gemini_newapi_cheap_first_policy.py tests/test_gemini_newapi_model_selector.py -q",
            ],
        }

    def _candidate_row(self, profile: ModelProfile, policy: TaskCandidatePolicy) -> dict[str, Any]:
        stable = profile.status == "stable"
        within_cost = _tier_rank(profile.cost_tier) <= _tier_rank(policy.max_default_cost_tier)
        pricing_status = _pricing_status(profile, policy.price_mode)
        price_value = _price_value(profile, policy.price_mode)
        default_eligible = stable and within_cost and pricing_status in {"token_priced", "image_priced"}
        preferred_hits = [capability for capability in policy.preferred_capabilities if capability in profile.capabilities]
        missing_preferred = [
            capability
            for capability in policy.preferred_capabilities
            if capability not in profile.capabilities
        ]
        return {
            "model_id": profile.id,
            "family": _family_label(profile.id),
            "catalog_status": profile.status,
            "cost_tier": profile.cost_tier,
            "latency_tier": profile.latency_tier,
            "pricing_status": pricing_status,
            "price_sort_value": None if price_value >= TEXT_PRICE_MISSING_PENALTY else price_value,
            "input_usd_per_million_tokens": profile.input_usd_per_million_tokens,
            "output_usd_per_million_tokens": profile.output_usd_per_million_tokens,
            "output_usd_per_image": profile.output_usd_per_image,
            "within_default_cost_tier": within_cost,
            "default_eligible": default_eligible,
            "preferred_capability_hits": preferred_hits,
            "missing_preferred_capabilities": missing_preferred,
            "capabilities": list(profile.capabilities),
            "sort_key": (
                0 if default_eligible else 1,
                0 if pricing_status in {"token_priced", "image_priced"} else 1,
                price_value,
                0 if stable else 1,
                _tier_rank(profile.cost_tier),
                LATENCY_RANK.get(profile.latency_tier, 99),
                -len(preferred_hits),
                profile.id,
            ),
        }

    def _ladder_role(self, candidate: dict[str, Any], policy: TaskCandidatePolicy) -> str:
        if not candidate["default_eligible"]:
            if candidate["catalog_status"] != "stable":
                return "explicit preview review"
            if candidate["pricing_status"] not in {"token_priced", "image_priced"}:
                return "explicit price review"
            return "operator-approved exception only"
        if policy.price_mode == "image":
            return "media default candidate" if len(policy.required_capabilities) == 1 else "media route candidate"
        if candidate["cost_tier"] in {"lowest", "low"}:
            return "cheap-first default candidate"
        return "operator-approved exception only"

    def _privacy_boundary(self) -> dict[str, Any]:
        return {
            "metadata_only": True,
            "gateway_called": False,
            "network_called": False,
            "configuration_written": False,
            "credentials_included": False,
            "prompts_included": False,
            "raw_legal_text_included": False,
            "raw_model_output_included": False,
            "output_scope": "local catalog model ids, capabilities, lifecycle status, price metadata, and task labels only",
        }


def normalize_task(task: str) -> str:
    value = str(task or "fast").strip().lower().replace("_", "-")
    return TASK_ALIASES.get(value, value)


def _has_required_capabilities(profile: ModelProfile, required: tuple[str, ...]) -> bool:
    return all(capability in profile.capabilities for capability in required)


def _pricing_status(profile: ModelProfile, price_mode: str) -> str:
    if price_mode == "image":
        return "image_priced" if profile.output_usd_per_image is not None else "missing"
    if profile.input_usd_per_million_tokens is not None and profile.output_usd_per_million_tokens is not None:
        return "token_priced"
    if profile.input_usd_per_million_tokens is not None or profile.output_usd_per_million_tokens is not None:
        return "partial_token_priced"
    return "missing"


def _price_value(profile: ModelProfile, price_mode: str) -> float:
    if price_mode == "image":
        return profile.output_usd_per_image if profile.output_usd_per_image is not None else TEXT_PRICE_MISSING_PENALTY
    if profile.input_usd_per_million_tokens is None or profile.output_usd_per_million_tokens is None:
        return TEXT_PRICE_MISSING_PENALTY
    return profile.input_usd_per_million_tokens + profile.output_usd_per_million_tokens


def _tier_rank(cost_tier: str) -> int:
    return COST_RANK.get(cost_tier, 99)


def _family_label(model_id: str) -> str:
    if "flash-lite" in model_id:
        return "gemini-flash-lite"
    if "flash" in model_id and "image" not in model_id:
        return "gemini-flash"
    if "pro" in model_id and "image" not in model_id:
        return "gemini-pro"
    if "image" in model_id:
        return "gemini-image"
    return "gemini"
