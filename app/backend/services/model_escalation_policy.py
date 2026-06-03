from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from services.model_budget import model_budget_decision, normalize_budget_task
from services.model_catalog import resolve_model, task_default_model


FAIL_SIGNALS = {
    "json_parse_error",
    "empty_output",
    "schema_missing_required",
    "citation_audit_fail",
    "evidence_audit_fail",
    "quality_gate_fail",
    "timeout",
}

WARN_SIGNALS = {
    "low_confidence",
    "needs_context",
    "weak_citations",
    "missing_facts",
    "long_document",
    "ocr_uncertain",
    "unknown_model_price",
}


@dataclass(frozen=True)
class EscalationStep:
    order: int
    mode: str
    task: str
    model_alias: str
    resolved_model: str
    trigger: str
    requires_operator_review: bool
    stop_after_failure: bool

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EscalationPlan:
    task: str
    display_name: str
    max_attempts: int
    hard_stop_signals: tuple[str, ...]
    steps: tuple[EscalationStep, ...]
    quality_signals: tuple[str, ...]
    rationale: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["hard_stop_signals"] = list(self.hard_stop_signals)
        data["steps"] = [step.to_api() for step in self.steps]
        data["quality_signals"] = list(self.quality_signals)
        return data


class ModelEscalationPolicyService:
    """Cheap-first deterministic escalation plans inspired by LLM cascade routing."""

    def build_policy(self) -> dict[str, Any]:
        plans = [plan.to_api() for plan in self._plans()]
        return {
            "status": "ready",
            "research_basis": [
                {
                    "id": "frugalgpt",
                    "url": "https://arxiv.org/abs/2305.05176",
                    "signal": "LLM cascades can reduce cost by starting with cheaper models and escalating hard queries.",
                },
                {
                    "id": "routing-cascading",
                    "url": "https://huggingface.co/papers/2410.10347",
                    "signal": "Routing and cascading both depend on quality estimators for cost-performance tradeoffs.",
                },
            ],
            "policy_notes": [
                "Start every high-volume task on the cheapest configured capable model.",
                "Escalate only on deterministic quality signals or explicit operator action.",
                "Never retry secrets, prompts, or raw documents in this policy object; it contains routing metadata only.",
                "Premium models remain exception paths for complex PDF, final review, or failed lower-tier attempts.",
            ],
            "plans": plans,
            "coverage": {
                "plan_count": len(plans),
                "tasks": [plan["task"] for plan in plans],
                "max_attempts": max(plan["max_attempts"] for plan in plans),
                "premium_escalation_tasks": [
                    plan["task"]
                    for plan in plans
                    if any(step["requires_operator_review"] for step in plan["steps"])
                ],
            },
        }

    def evaluate(self, task: str, signals: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
        normalized_task = normalize_budget_task(task)
        plan = self._plan_by_task(normalized_task)
        signal_set = {str(signal).strip().lower() for signal in (signals or []) if str(signal).strip()}
        if not plan:
            return {
                "task": normalized_task,
                "decision": "use-budget-policy",
                "next_step": None,
                "reasons": ["No dedicated escalation plan; use standard model budget policy."],
            }

        hard_stops = sorted(signal_set.intersection(plan.hard_stop_signals))
        if hard_stops:
            return {
                "task": normalized_task,
                "decision": "stop",
                "next_step": None,
                "reasons": [f"Hard-stop signal present: {signal}." for signal in hard_stops],
            }

        fail_hits = sorted(signal_set.intersection(FAIL_SIGNALS))
        warn_hits = sorted(signal_set.intersection(WARN_SIGNALS))
        if fail_hits:
            step = self._step(plan, mode="retry-up")
            return {
                "task": normalized_task,
                "decision": "escalate",
                "next_step": step.to_api() if step else None,
                "reasons": [f"Failure signal present: {signal}." for signal in fail_hits],
            }
        if warn_hits:
            step = self._step(plan, mode="verify")
            return {
                "task": normalized_task,
                "decision": "verify",
                "next_step": step.to_api() if step else None,
                "reasons": [f"Warning signal present: {signal}." for signal in warn_hits],
            }

        first_step = plan.steps[0]
        return {
            "task": normalized_task,
            "decision": "continue",
            "next_step": first_step.to_api(),
            "reasons": ["No escalation signal detected; continue cheap-first route."],
        }

    def _plans(self) -> tuple[EscalationPlan, ...]:
        return (
            self._plan(
                task="fast",
                display_name="Fast routing and preflight",
                aliases=("auto-fast", "auto-review"),
                max_attempts=2,
                hard_stop_signals=("privacy_high", "instruction_high"),
                quality_signals=("json_parse_error", "empty_output", "low_confidence"),
                rationale="Cheap routing should retry once on the balanced review model only when deterministic parsing or confidence checks fail.",
            ),
            self._plan(
                task="ocr",
                display_name="OCR and extraction assist",
                aliases=("auto-ocr", "auto-review"),
                max_attempts=2,
                hard_stop_signals=("privacy_high",),
                quality_signals=("empty_output", "ocr_uncertain", "low_confidence"),
                rationale="OCR uses Flash-Lite first and escalates only when extracted text quality is too weak for review.",
            ),
            self._plan(
                task="review",
                display_name="Legal review",
                aliases=("auto-review", "auto-pdf"),
                max_attempts=2,
                hard_stop_signals=("privacy_high", "instruction_high"),
                quality_signals=("citation_audit_fail", "evidence_audit_fail", "quality_gate_fail", "weak_citations"),
                rationale="Balanced review is default; premium escalation is reserved for failed quality, citation, or evidence gates.",
            ),
            self._plan(
                task="pdf",
                display_name="Large PDF and final review",
                aliases=("auto-pdf",),
                max_attempts=1,
                hard_stop_signals=("extraction_quality_fail", "privacy_high", "instruction_high"),
                quality_signals=("long_document", "timeout", "quality_gate_fail"),
                rationale="Complex PDFs already use the premium exception path; hard-stop signals prevent wasteful retries.",
            ),
            self._plan(
                task="classification",
                display_name="Material classification",
                aliases=("auto-fast", "auto-review"),
                max_attempts=2,
                hard_stop_signals=("privacy_high",),
                quality_signals=("schema_missing_required", "low_confidence"),
                rationale="Classification should stay cheap unless schema completeness or confidence checks fail.",
            ),
        )

    def _plan(
        self,
        *,
        task: str,
        display_name: str,
        aliases: tuple[str, ...],
        max_attempts: int,
        hard_stop_signals: tuple[str, ...],
        quality_signals: tuple[str, ...],
        rationale: str,
    ) -> EscalationPlan:
        steps = tuple(
            EscalationStep(
                order=index + 1,
                mode="start" if index == 0 else ("retry-up" if alias == "auto-pdf" else "verify"),
                task=task,
                model_alias=alias,
                resolved_model=resolve_model(alias, task=task),
                trigger="initial attempt" if index == 0 else "quality signal",
                requires_operator_review=model_budget_decision(alias, task=task).requires_operator_review
                or (alias == "auto-pdf" and task != "pdf"),
                stop_after_failure=index + 1 >= max_attempts,
            )
            for index, alias in enumerate(aliases[:max_attempts])
        )
        return EscalationPlan(
            task=task,
            display_name=display_name,
            max_attempts=max_attempts,
            hard_stop_signals=hard_stop_signals,
            steps=steps,
            quality_signals=quality_signals,
            rationale=rationale,
        )

    def _plan_by_task(self, task: str) -> EscalationPlan | None:
        for plan in self._plans():
            if plan.task == task:
                return plan
        return None

    def _step(self, plan: EscalationPlan, *, mode: str) -> EscalationStep | None:
        for step in plan.steps:
            if step.mode == mode:
                return step
        return plan.steps[-1] if plan.steps else None
