from __future__ import annotations

from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_catalog import canonical_model_id, model_profile, task_default_model


TASK_ENV_VARS: dict[str, str] = {
    "cheap": "APP_AI_CHEAP_MODEL",
    "fast": "APP_AI_FAST_MODEL",
    "ocr": "APP_OCR_MODEL",
    "classification": "APP_AI_CLASSIFIER_MODEL",
    "review": "APP_AI_REVIEW_MODEL",
    "pdf": "APP_AI_PDF_MODEL",
    "image": "APP_AI_IMAGE_MODEL",
    "agentic": "APP_AI_AGENTIC_MODEL",
    "grounded-research": "APP_AI_GROUNDED_RESEARCH_MODEL",
}

PREMIUM_EXCEPTION_TASKS = {"pdf", "image"}


class ModelOpsGeminiDefaultChangeReviewService:
    """Review proposed Gemini default changes without applying configuration."""

    def __init__(self, capability_matrix_service: ModelCapabilityMatrixService | None = None) -> None:
        self.capability_matrix_service = capability_matrix_service or ModelCapabilityMatrixService()

    def build_review(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        proposed_changes = self._proposed_changes(payload)
        capability_matrix = self.capability_matrix_service.build_matrix()
        matrix_rows = {
            str(row.get("task")): row
            for row in _list(capability_matrix.get("tasks"))
            if isinstance(row, dict)
        }
        rows = [self._review_row(item, matrix_rows) for item in proposed_changes]
        blocked = [row for row in rows if row["review_status"] == "blocked"]
        review = [row for row in rows if row["review_status"] == "review_required"]
        ready = [row for row in rows if row["review_status"] == "ready"]
        status = "blocked" if blocked else ("review_required" if review else "ready")

        return {
            "status": status,
            "method": {
                "type": "model-ops-gemini-default-change-review",
                "notes": [
                    "Evaluates maintainer-supplied default model proposals against local Gemini metadata only.",
                    "Designed for review before any .env edit, default-change queue promotion, or canary plan.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, or the network.",
                ],
            },
            "summary": {
                "proposal_count": len(rows),
                "ready_count": len(ready),
                "review_required_count": len(review),
                "blocked_count": len(blocked),
                "known_model_count": sum(1 for row in rows if row["proposed_model_known"]),
                "unknown_model_count": sum(1 for row in rows if not row["proposed_model_known"]),
                "cheap_first_regression_count": sum(1 for row in rows if row["cheap_first_regression"]),
                "premium_exception_count": sum(1 for row in rows if row["premium_exception"]),
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
            },
            "proposal_rows": rows,
            "blocking_proposal_ids": [row["id"] for row in blocked],
            "review_proposal_ids": [row["id"] for row in review],
            "recommended_actions": self._recommended_actions(blocked, review, ready),
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "real_env_read": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "prompts_included": False,
                "raw_payload_echoed": False,
                "raw_legal_text_included": False,
                "model_outputs_included": False,
                "output_scope": "task ids, env var names, model ids, status labels, reason codes, and validation commands",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "live_gateway_execution_claimed": False,
                "production_quality_claimed": False,
                "public_benchmark_scores_included": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_default_change_review.py tests/test_model_ops_default_change_queue.py -q",
                "python -m pytest tests/test_modelops_gemini_cheap_first_coverage_gate.py tests/test_model_capability_matrix.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _proposed_changes(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        raw = payload.get("proposed_changes")
        if isinstance(raw, list) and raw:
            return [item for item in raw[:20] if isinstance(item, dict)]
        return [
            {
                "task": "agentic",
                "env_var": TASK_ENV_VARS["agentic"],
                "current_model": task_default_model("agentic"),
                "proposed_model": task_default_model("agentic"),
                "review_note": "current cheap-first agentic default",
            },
            {
                "task": "grounded-research",
                "env_var": TASK_ENV_VARS["grounded-research"],
                "current_model": task_default_model("grounded-research"),
                "proposed_model": task_default_model("grounded-research"),
                "review_note": "current cheap-first grounded research default",
            },
        ]

    def _review_row(self, item: dict[str, Any], matrix_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
        task = _normalize_task(str(item.get("task") or "fast"))
        env_var = str(item.get("env_var") or TASK_ENV_VARS.get(task, "APP_AI_MODEL"))
        current_model = str(item.get("current_model") or task_default_model(task))
        proposed_model = str(item.get("proposed_model") or current_model)
        current_profile = model_profile(current_model)
        proposed_profile = model_profile(proposed_model)
        matrix_row = matrix_rows.get(task) or {}
        requirement = matrix_row.get("requirement") if isinstance(matrix_row.get("requirement"), dict) else {}
        recommended_model = str(matrix_row.get("recommended_model") or task_default_model(task))
        max_cost_tier = str(requirement.get("max_cost_tier") or ("premium" if task in PREMIUM_EXCEPTION_TASKS else "low"))
        required_capabilities = [str(cap) for cap in _list(requirement.get("required_capabilities"))]
        missing_required = [
            cap
            for cap in required_capabilities
            if proposed_profile is None or cap not in proposed_profile.capabilities
        ]
        current_cost = current_profile.cost_tier if current_profile else "unknown"
        proposed_cost = proposed_profile.cost_tier if proposed_profile else "unknown"
        premium_exception = task in PREMIUM_EXCEPTION_TASKS or _tier_rank(proposed_cost) > _tier_rank(max_cost_tier)
        cheap_first_regression = (
            task not in PREMIUM_EXCEPTION_TASKS
            and current_profile is not None
            and proposed_profile is not None
            and _tier_rank(proposed_cost) > _tier_rank(current_cost)
        )
        reason_codes = self._reason_codes(
            task=task,
            proposed_model=proposed_model,
            proposed_profile=proposed_profile,
            proposed_cost=proposed_cost,
            max_cost_tier=max_cost_tier,
            missing_required=missing_required,
            premium_exception=premium_exception,
            cheap_first_regression=cheap_first_regression,
            recommended_model=recommended_model,
        )
        review_status = self._review_status(reason_codes)
        return {
            "id": f"gemini-default-change-review-{task}",
            "task": task,
            "env_var": env_var,
            "current_model": current_model,
            "current_canonical_model": canonical_model_id(current_model),
            "proposed_model": proposed_model,
            "proposed_canonical_model": canonical_model_id(proposed_model),
            "recommended_model": recommended_model,
            "review_status": review_status,
            "release_action": self._release_action(review_status),
            "current_cost_tier": current_cost,
            "proposed_cost_tier": proposed_cost,
            "max_cost_tier": max_cost_tier,
            "proposed_model_known": proposed_profile is not None,
            "proposed_model_status": proposed_profile.status if proposed_profile else "unknown",
            "proposed_model_family": proposed_profile.family if proposed_profile else ("gemini-like" if "gemini" in proposed_model.lower() else "unknown"),
            "required_capabilities": required_capabilities,
            "missing_required_capabilities": missing_required,
            "cheap_first_regression": cheap_first_regression,
            "premium_exception": premium_exception,
            "reason_codes": reason_codes,
            "review_note": _safe_note(item.get("review_note")),
        }

    def _reason_codes(
        self,
        *,
        task: str,
        proposed_model: str,
        proposed_profile: Any,
        proposed_cost: str,
        max_cost_tier: str,
        missing_required: list[str],
        premium_exception: bool,
        cheap_first_regression: bool,
        recommended_model: str,
    ) -> list[str]:
        codes: list[str] = []
        if proposed_profile is None:
            if _is_gemini_like(proposed_model):
                codes.append("unknown-gemini-catalog-metadata")
            else:
                codes.append("non-gemini-or-unknown-model")
        elif proposed_profile.status != "stable":
            codes.append(f"lifecycle-{proposed_profile.status}")
        if missing_required:
            codes.append("missing-required-capabilities")
        if _tier_rank(proposed_cost) > _tier_rank(max_cost_tier):
            codes.append("over-task-cost-budget")
        if cheap_first_regression:
            codes.append(
                "high-volume-cheap-first-regression"
                if task in {"fast", "ocr", "classification"}
                else "cheap-first-cost-regression"
            )
        if premium_exception:
            codes.append("manual-premium-exception-review")
        if proposed_model != recommended_model and not premium_exception:
            codes.append("not-current-cheapest-capable-recommendation")
        return codes or ["proposal-ready"]

    def _review_status(self, reason_codes: list[str]) -> str:
        blocking = {
            "non-gemini-or-unknown-model",
            "missing-required-capabilities",
            "high-volume-cheap-first-regression",
        }
        if any(code in blocking for code in reason_codes):
            return "blocked"
        if any(code != "proposal-ready" for code in reason_codes):
            return "review_required"
        return "ready"

    def _release_action(self, review_status: str) -> str:
        if review_status == "ready":
            return "eligible_for_default_change_queue_review"
        if review_status == "blocked":
            return "block_env_default_change"
        return "require_maintainer_review_before_env_change"

    def _recommended_actions(
        self,
        blocked: list[dict[str, Any]],
        review: list[dict[str, Any]],
        ready: list[dict[str, Any]],
    ) -> list[str]:
        if blocked:
            return [
                "Keep blocked proposals out of default environment templates until capability and cheap-first gaps are resolved.",
                "Use explicit per-request model overrides for experiments with unknown or higher-cost Gemini variants.",
            ]
        if review:
            return [
                "Complete maintainer review for lifecycle, pricing, gateway, and premium-exception signals before editing defaults.",
                "Route approved proposals through the default-change queue, canary plan, and rollback drill evidence.",
            ]
        if ready:
            return ["Ready proposals can move to default-change queue review after validation commands pass."]
        return ["Submit sanitized proposal metadata before changing Gemini defaults."]


def _normalize_task(task: str) -> str:
    value = (task or "fast").strip().lower().replace("_", "-")
    aliases = {
        "classifier": "classification",
        "legal-review": "review",
        "chat": "review",
        "workflow-planning": "agentic",
        "rag-research": "grounded-research",
        "research": "grounded-research",
        "genimg": "image",
        "visual": "image",
    }
    return aliases.get(value, value)


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)


def _is_gemini_like(model: str) -> bool:
    value = (model or "").strip().lower()
    return value.startswith("gemini-") or "/gemini-" in value or ":gemini-" in value


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_note(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    forbidden = ("sk-", "api_key", "authorization", "password", "secret", "prompt", "payload", "@")
    if any(marker in text.lower() for marker in forbidden):
        return "redacted-sensitive-review-note"
    return text[:160]
