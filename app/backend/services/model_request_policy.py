from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import TASK_GROUPS, normalize_budget_task


@dataclass(frozen=True)
class GenerationTaskPolicy:
    task: str
    default_temperature: float
    max_temperature: float
    default_max_tokens: int
    max_max_tokens: int
    rationale: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GenerationRequestPolicyDecision:
    task: str
    requested_temperature: float | None
    effective_temperature: float
    requested_max_tokens: int | None
    effective_max_tokens: int
    temperature_adjusted: bool
    max_tokens_adjusted: bool
    response_format_mode: str
    cost_mode: str
    reason: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


TASK_PARAMETER_POLICIES: dict[str, GenerationTaskPolicy] = {
    "fast": GenerationTaskPolicy(
        task="fast",
        default_temperature=0.1,
        max_temperature=0.5,
        default_max_tokens=1024,
        max_max_tokens=4096,
        rationale="High-volume routing and preflight tasks should keep outputs short unless the caller asks for more.",
    ),
    "ocr": GenerationTaskPolicy(
        task="ocr",
        default_temperature=0.0,
        max_temperature=0.2,
        default_max_tokens=2048,
        max_max_tokens=4096,
        rationale="OCR fallback should be deterministic while allowing enough output for scanned pages.",
    ),
    "classification": GenerationTaskPolicy(
        task="classification",
        default_temperature=0.0,
        max_temperature=0.2,
        default_max_tokens=768,
        max_max_tokens=1536,
        rationale="Classification should produce compact deterministic JSON or labels on the cheapest model.",
    ),
    "review": GenerationTaskPolicy(
        task="review",
        default_temperature=0.2,
        max_temperature=0.7,
        default_max_tokens=4096,
        max_max_tokens=10000,
        rationale="Legal review needs enough space for structured analysis while avoiding premium-style verbosity by default.",
    ),
    "grounded-research": GenerationTaskPolicy(
        task="grounded-research",
        default_temperature=0.1,
        max_temperature=0.5,
        default_max_tokens=4096,
        max_max_tokens=8000,
        rationale="Grounded research needs enough room for source-aware answers while keeping the low-cost default bounded.",
    ),
    "agentic": GenerationTaskPolicy(
        task="agentic",
        default_temperature=0.0,
        max_temperature=0.4,
        default_max_tokens=2048,
        max_max_tokens=4096,
        rationale="Agentic planning should stay deterministic and compact before any tool or workflow execution.",
    ),
    "pdf": GenerationTaskPolicy(
        task="pdf",
        default_temperature=0.0,
        max_temperature=0.4,
        default_max_tokens=8192,
        max_max_tokens=12000,
        rationale="PDF and complex review paths are premium exceptions, but deterministic output still limits retry risk.",
    ),
    "image": GenerationTaskPolicy(
        task="image",
        default_temperature=0.0,
        max_temperature=0.0,
        default_max_tokens=0,
        max_max_tokens=0,
        rationale="Media generation endpoints use separate request controls.",
    ),
}


def resolve_generation_request_policy(
    *,
    task: str,
    requested_temperature: float | None = None,
    requested_max_tokens: int | None = None,
    response_format: dict[str, Any] | None = None,
) -> GenerationRequestPolicyDecision:
    """Choose task-aware chat-completion parameters before sending a gateway request."""

    normalized_task = normalize_budget_task(task)
    policy = TASK_PARAMETER_POLICIES.get(normalized_task, TASK_PARAMETER_POLICIES["review"])
    response_format_mode = _response_format_mode(response_format)
    max_temperature = min(policy.max_temperature, 0.2) if response_format_mode == "json" else policy.max_temperature

    effective_temperature = _clamp_float(
        policy.default_temperature if requested_temperature is None else requested_temperature,
        minimum=0.0,
        maximum=max_temperature,
    )
    effective_max_tokens = _clamp_int(
        policy.default_max_tokens if requested_max_tokens is None else requested_max_tokens,
        minimum=1 if policy.max_max_tokens > 0 else 0,
        maximum=policy.max_max_tokens,
    )
    temperature_adjusted = (
        requested_temperature is not None and round(float(requested_temperature), 4) != effective_temperature
    )
    max_tokens_adjusted = requested_max_tokens is not None and int(requested_max_tokens) != effective_max_tokens

    return GenerationRequestPolicyDecision(
        task=normalized_task,
        requested_temperature=requested_temperature,
        effective_temperature=effective_temperature,
        requested_max_tokens=requested_max_tokens,
        effective_max_tokens=effective_max_tokens,
        temperature_adjusted=temperature_adjusted,
        max_tokens_adjusted=max_tokens_adjusted,
        response_format_mode=response_format_mode,
        cost_mode=_cost_mode(policy, requested_max_tokens),
        reason=_reason(
            policy=policy,
            response_format_mode=response_format_mode,
            temperature_adjusted=temperature_adjusted,
            max_tokens_adjusted=max_tokens_adjusted,
        ),
    )


def generation_request_policy_for_api() -> dict[str, Any]:
    decisions = [
        resolve_generation_request_policy(task=task).to_api()
        for task in TASK_GROUPS
        if task != "image"
    ]
    return {
        "status": "ready",
        "request_fields": {
            "temperature": "Policy default and ceiling for sampling randomness by route.",
            "max_tokens": "Policy output token default and ceiling before gateway dispatch.",
            "response_format": "JSON response_format lowers the temperature ceiling for deterministic structured output.",
        },
        "policy_notes": [
            "Omitted temperature and max_tokens now use route policy defaults instead of a single global value.",
            "Classification and OCR keep deterministic low-token defaults for cheap Gemini routes.",
            "Review and PDF routes preserve larger explicit output budgets because those stages need structured legal analysis.",
            "JSON response_format lowers the temperature ceiling to reduce malformed structured output and retries.",
        ],
        "task_defaults": decisions,
        "task_policies": [policy.to_api() for policy in TASK_PARAMETER_POLICIES.values() if policy.task != "image"],
    }


def _response_format_mode(response_format: dict[str, Any] | None) -> str:
    if not isinstance(response_format, dict):
        return "text"
    value = str(response_format.get("type") or "").strip().lower()
    if "json" in value:
        return "json"
    return "text"


def _clamp_float(value: float, *, minimum: float, maximum: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = minimum
    return round(max(minimum, min(numeric, maximum)), 4)


def _clamp_int(value: int, *, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = minimum
    if maximum <= 0:
        return 0
    return max(minimum, min(numeric, maximum))


def _cost_mode(policy: GenerationTaskPolicy, requested_max_tokens: int | None) -> str:
    if requested_max_tokens is None:
        return "policy-default"
    if requested_max_tokens > policy.default_max_tokens:
        return "caller-expanded"
    if requested_max_tokens < policy.default_max_tokens:
        return "caller-reduced"
    return "policy-default"


def _reason(
    *,
    policy: GenerationTaskPolicy,
    response_format_mode: str,
    temperature_adjusted: bool,
    max_tokens_adjusted: bool,
) -> str:
    notes = [policy.rationale]
    if response_format_mode == "json":
        notes.append("JSON output lowers the temperature ceiling to reduce parse failures and retries.")
    if temperature_adjusted:
        notes.append("Requested temperature was clamped to the task ceiling.")
    if max_tokens_adjusted:
        notes.append("Requested max_tokens was clamped to the task ceiling.")
    return " ".join(notes)
