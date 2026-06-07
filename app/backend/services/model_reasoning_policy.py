from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from services.model_budget import TASK_GROUPS, normalize_budget_task
from services.model_catalog import task_default_model


MEDIA_ENDPOINT_TASKS = {"image", "video", "audio", "transcription"}


ReasoningEffort = Literal["auto", "none", "minimal", "low", "medium", "high"]

SUPPORTED_REASONING_EFFORTS: tuple[ReasoningEffort, ...] = (
    "auto",
    "none",
    "minimal",
    "low",
    "medium",
    "high",
)


@dataclass(frozen=True)
class ReasoningPolicyDecision:
    task: str
    model: str
    requested_effort: str | None
    effective_effort: str | None
    gateway_parameter: str | None
    source: str
    adjusted: bool
    supported_efforts: tuple[str, ...]
    cost_mode: str
    reason: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["supported_efforts"] = list(self.supported_efforts)
        return data


def resolve_reasoning_effort(
    *,
    model: str,
    task: str,
    requested_effort: str | None = None,
) -> ReasoningPolicyDecision:
    """Choose an OpenAI-compatible reasoning_effort value for Gemini chat calls."""

    normalized_task = normalize_budget_task(task)
    requested = _normalize_requested_effort(requested_effort)
    supported = _supported_efforts_for_model(model)
    if not supported:
        return ReasoningPolicyDecision(
            task=normalized_task,
            model=model,
            requested_effort=requested_effort,
            effective_effort=None,
            gateway_parameter=None,
            source="omitted",
            adjusted=False,
            supported_efforts=(),
            cost_mode="not-applicable",
            reason="No Gemini reasoning-effort profile is known for this model; omit provider-specific parameter.",
        )

    default_effort = _default_effort_for_task(normalized_task, supported)
    source = "request" if requested and requested != "auto" else "default"
    desired = requested if requested and requested != "auto" else default_effort
    effective = _coerce_effort(desired, supported)
    adjusted = bool(desired and desired != effective)

    return ReasoningPolicyDecision(
        task=normalized_task,
        model=model,
        requested_effort=requested_effort,
        effective_effort=effective,
        gateway_parameter=effective if effective != "auto" else None,
        source=source,
        adjusted=adjusted,
        supported_efforts=supported,
        cost_mode=_cost_mode(effective),
        reason=_reason(
            task=normalized_task,
            model=model,
            desired=desired,
            effective=effective,
            source=source,
            adjusted=adjusted,
        ),
    )


def reasoning_policy_for_api() -> dict[str, Any]:
    decisions = [
        resolve_reasoning_effort(model=task_default_model(task), task=task).to_api()
        for task in TASK_GROUPS
        if task not in MEDIA_ENDPOINT_TASKS
    ]
    return {
        "status": "ready",
        "request_field": {
            "name": "reasoning_effort",
            "values": list(SUPPORTED_REASONING_EFFORTS),
            "default": "auto",
        },
        "policy_notes": [
            "High-volume fast, OCR, and classification tasks disable or minimize thinking when the model supports it.",
            "Legal review defaults to low reasoning effort to preserve quality without making premium-style thinking the default.",
            "PDF and complex review tasks use high reasoning effort because they are already premium-exception paths.",
            "Unknown gateway models keep the parameter omitted so NewAPI/Gemini-compatible pass-through remains safe.",
            "Unsupported requested efforts are coerced to the cheapest supported safe effort.",
        ],
        "task_defaults": decisions,
    }


def _normalize_requested_effort(value: str | None) -> ReasoningEffort | None:
    normalized = (value or "").strip().lower()
    return normalized if normalized in SUPPORTED_REASONING_EFFORTS else None  # type: ignore[return-value]


def _supported_efforts_for_model(model: str) -> tuple[str, ...]:
    value = (model or "").strip().lower()
    if not value.startswith("gemini-"):
        return ()
    if value.startswith("gemini-2.5-pro"):
        return ("low", "medium", "high")
    if value.startswith("gemini-2.5-"):
        return ("none", "minimal", "low", "medium", "high")
    if value.startswith("gemini-3") and "pro" in value:
        return ("low", "high")
    if value.startswith("gemini-3") and ("flash" in value or "lite" in value):
        return ("minimal", "low", "medium", "high")
    if value.startswith("gemini-3"):
        return ("minimal", "low", "medium", "high")
    return ()


def _default_effort_for_task(task: str, supported: tuple[str, ...]) -> str:
    if task in {"fast", "ocr", "classification"}:
        if "none" in supported:
            return "none"
        if "minimal" in supported:
            return "minimal"
        return "low"
    if task == "pdf":
        return "high" if "high" in supported else supported[-1]
    if task == "review":
        return "low" if "low" in supported else supported[0]
    return "low" if "low" in supported else supported[0]


def _coerce_effort(desired: str | None, supported: tuple[str, ...]) -> str:
    if desired and desired in supported:
        return desired
    if desired in {"none", "minimal", "medium"} and "low" in supported:
        return "low"
    if desired == "high" and "high" in supported:
        return "high"
    if "minimal" in supported:
        return "minimal"
    if "low" in supported:
        return "low"
    return supported[0]


def _cost_mode(effort: str | None) -> str:
    if effort is None:
        return "omitted"
    if effort == "none":
        return "thinking-disabled"
    if effort == "minimal":
        return "minimal-thinking"
    if effort == "low":
        return "low-thinking"
    return "elevated-thinking"


def _reason(
    *,
    task: str,
    model: str,
    desired: str | None,
    effective: str,
    source: str,
    adjusted: bool,
) -> str:
    if adjusted:
        return (
            f"Requested reasoning_effort={desired} is not supported for {model}; "
            f"using {effective} for the {task} route."
        )
    if source == "request":
        return f"Using requested reasoning_effort={effective} for the {task} route."
    if task in {"fast", "ocr", "classification"}:
        return f"Using {effective} reasoning to keep high-volume {task} calls cheap."
    if task == "pdf":
        return "Using high reasoning for premium-exception PDF or complex review work."
    return f"Using {effective} reasoning for balanced legal review quality and cost."
