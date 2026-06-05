from __future__ import annotations

from typing import Any

from services.model_budget import COST_TIER_RANK
from services.model_capability_matrix import ModelCapabilityMatrixService
from services.model_catalog import canonical_model_id, model_profile, task_default_model
from services.model_gateway_compatibility import ModelGatewayCompatibilityService
from services.model_lifecycle_policy import ModelLifecyclePolicyService
from services.model_reasoning_policy import resolve_reasoning_effort


CHEAP_FIRST_TASKS = {"fast", "ocr", "classification", "agentic", "grounded-research"}
BALANCED_TASKS = {"review"}
PREMIUM_EXCEPTION_TASKS = {"pdf", "image"}


class ModelOpsGeminiCheapFirstCoverageGateService:
    """Build metadata-only coverage evidence for Gemini cheap-first defaults."""

    def __init__(
        self,
        *,
        capability_matrix_service: ModelCapabilityMatrixService | None = None,
        lifecycle_policy_service: ModelLifecyclePolicyService | None = None,
        gateway_compatibility_service: ModelGatewayCompatibilityService | None = None,
    ) -> None:
        self.capability_matrix_service = capability_matrix_service or ModelCapabilityMatrixService()
        self.lifecycle_policy_service = lifecycle_policy_service or ModelLifecyclePolicyService()
        self.gateway_compatibility_service = gateway_compatibility_service or ModelGatewayCompatibilityService()

    def build_gate(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        capability_matrix = _dict_or(data.get("capability_matrix"), self.capability_matrix_service.build_matrix())
        lifecycle_policy = _dict_or(data.get("lifecycle_policy"), self.lifecycle_policy_service.build_policy())
        gateway_compatibility = _dict_or(data.get("gateway_compatibility"), self.gateway_compatibility_service.evaluate())
        rows = [
            self._coverage_row(row, lifecycle_policy, gateway_compatibility)
            for row in _list(capability_matrix.get("tasks"))
            if isinstance(row, dict)
        ]
        blocked = [row for row in rows if row["coverage_status"] == "blocked"]
        review = [row for row in rows if row["coverage_status"] == "review_required"]
        ready = [row for row in rows if row["coverage_status"] == "ready"]

        status = "blocked" if blocked else ("review_required" if review else "pass")
        return {
            "id": "modelops-gemini-cheap-first-coverage-gate",
            "title": "ModelOps Gemini cheap-first coverage gate",
            "status": status,
            "summary": {
                "coverage_row_count": len(rows),
                "ready_row_count": len(ready),
                "review_row_count": len(review),
                "blocked_row_count": len(blocked),
                "cheap_first_ready_count": sum(1 for row in rows if row["cheap_first_aligned"] and not row["premium_exception"]),
                "premium_exception_count": sum(1 for row in rows if row["premium_exception"]),
                "unknown_model_count": sum(1 for row in rows if row["model_family"] == "unknown"),
                "non_gemini_default_count": sum(1 for row in rows if row["model_family"] not in {"gemini", "media", "unknown"}),
                "missing_price_count": sum(1 for row in rows if row["price_status"] == "missing"),
                "missing_reasoning_policy_count": sum(1 for row in rows if row["reasoning_policy_status"] == "missing"),
                "gateway_review_count": sum(1 for row in rows if row["gateway_compatibility_status"] != "pass"),
                "lifecycle_review_count": sum(1 for row in rows if row["lifecycle_status"] != "stable"),
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "credentials_included": False,
            },
            "coverage_rows": rows,
            "research_basis": [
                {
                    "id": "gemini-openai-compatibility",
                    "url": "https://ai.google.dev/gemini-api/docs/openai",
                    "signal": "Gemini can be reached through OpenAI-compatible client configuration, including model names and base URLs.",
                },
                {
                    "id": "gemini-models",
                    "url": "https://ai.google.dev/gemini-api/docs/models",
                    "signal": "Gemini model families expose Flash-Lite, Flash, Pro, and media-specific variants with different capability roles.",
                },
                {
                    "id": "gemini-pricing",
                    "url": "https://ai.google.dev/gemini-api/docs/pricing",
                    "signal": "Flash-Lite style routes are substantially cheaper than Flash and Pro routes and should remain high-volume defaults.",
                },
            ],
            "linked_signal_summary": {
                "capability_matrix_status": capability_matrix.get("status", "unknown"),
                "lifecycle_policy_status": lifecycle_policy.get("status", "unknown"),
                "gateway_compatibility_status": gateway_compatibility.get("status", "unknown"),
                "capability_task_count": len(_list(capability_matrix.get("tasks"))),
                "configured_gateway_role_count": len(_list(gateway_compatibility.get("configured_roles"))),
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "public_benchmark_score_claimed": False,
                "production_quality_claimed": False,
                "automatic_default_change_claimed": False,
                "twenty_four_hour_completion_claimed": False,
                "allowed_claims": [
                    "The local ModelOps payload exposes metadata-only Gemini cheap-first coverage rows.",
                    "The gate links runtime defaults, recommended models, lifecycle, pricing, reasoning, and gateway compatibility metadata.",
                ],
                "forbidden_claims": [
                    "Do not claim a live NewAPI, Gemini, Google, OpenAI, or gateway probe was executed.",
                    "Do not claim public benchmark scores, production routing quality, or automatic default edits.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "returns_raw_prompt": False,
                "returns_raw_payload": False,
                "returns_gateway_payload": False,
                "returns_model_output": False,
                "returns_credentials": False,
                "returns_emails": False,
                "output_scope": "task ids, model ids, status labels, counts, reason codes, linked gate ids, and validation commands",
            },
            "recommended_actions": self._recommended_actions(blocked, review),
            "validation_commands": [
                "python -m pytest tests/test_modelops_gemini_cheap_first_coverage_gate.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_model_capability_matrix.py tests/test_model_lifecycle_policy.py tests/test_model_gateway_compatibility.py tests/test_model_reasoning_policy.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _coverage_row(
        self,
        matrix_row: dict[str, Any],
        lifecycle_policy: dict[str, Any],
        gateway_compatibility: dict[str, Any],
    ) -> dict[str, Any]:
        task = str(matrix_row.get("task") or "unknown")
        requirement = matrix_row.get("requirement") if isinstance(matrix_row.get("requirement"), dict) else {}
        runtime_default = str(matrix_row.get("runtime_default_model") or task_default_model(task))
        recommended = str(matrix_row.get("recommended_model") or runtime_default)
        profile = model_profile(runtime_default)
        recommended_profile = model_profile(recommended)
        role = self._role_for_task(task)
        lifecycle = self._lifecycle_status(runtime_default, lifecycle_policy)
        gateway_status = self._gateway_status(runtime_default, gateway_compatibility)
        reasoning = resolve_reasoning_effort(model=runtime_default, task=task)
        price_status = self._price_status(profile)
        cheap_first_aligned = self._cheap_first_aligned(task, profile, recommended_profile, runtime_default, recommended)
        premium_exception = role == "premium_exception"
        reason_codes = self._reason_codes(
            task=task,
            runtime_profile=profile,
            recommended_profile=recommended_profile,
            runtime_default=runtime_default,
            recommended=recommended,
            lifecycle_status=lifecycle,
            price_status=price_status,
            reasoning_policy_status="ready" if reasoning.gateway_parameter or reasoning.effective_effort else "missing",
            gateway_status=gateway_status,
            cheap_first_aligned=cheap_first_aligned,
            premium_exception=premium_exception,
        )
        coverage_status = self._coverage_status(reason_codes, premium_exception)
        return {
            "id": f"gemini-cheap-first-coverage-{task}",
            "task": task,
            "role": role,
            "runtime_default_model": runtime_default,
            "runtime_canonical_model": canonical_model_id(runtime_default),
            "recommended_model": recommended,
            "recommended_canonical_model": canonical_model_id(recommended),
            "coverage_status": coverage_status,
            "release_action": self._release_action(coverage_status, premium_exception),
            "cheap_first_aligned": cheap_first_aligned,
            "premium_exception": premium_exception,
            "model_family": self._model_family(profile, task),
            "cost_tier": profile.cost_tier if profile else "unknown",
            "max_cost_tier": str(requirement.get("max_cost_tier") or "premium"),
            "lifecycle_status": lifecycle,
            "price_status": price_status,
            "reasoning_policy_status": "ready" if reasoning.gateway_parameter or reasoning.effective_effort else "missing",
            "reasoning_effort": reasoning.gateway_parameter or reasoning.effective_effort,
            "reasoning_cost_mode": reasoning.cost_mode,
            "gateway_compatibility_status": gateway_status,
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "modelops-gemini-cheap-first-coverage-gate",
                "capability-matrix",
                "gemini-lifecycle-policy",
                "gateway-compatibility",
                "reasoning-policy",
                "cheap-first-calibration",
                "model-ops-readiness",
            ],
            "privacy_boundary": {
                "raw_prompt_returned": False,
                "raw_payload_returned": False,
                "model_output_returned": False,
                "credentials_returned": False,
            },
        }

    def _role_for_task(self, task: str) -> str:
        if task in CHEAP_FIRST_TASKS:
            return "cheap_first_default"
        if task in BALANCED_TASKS:
            return "balanced_after_precheck"
        if task in PREMIUM_EXCEPTION_TASKS:
            return "premium_exception"
        return "explicit_review"

    def _lifecycle_status(self, model: str, lifecycle_policy: dict[str, Any]) -> str:
        roles = _list(lifecycle_policy.get("configured_roles"))
        canonical = canonical_model_id(model)
        for role in roles:
            if not isinstance(role, dict):
                continue
            if role.get("model") == model or role.get("canonical_model") == canonical:
                return str(role.get("lifecycle_state") or role.get("model_status") or "unknown")
        profile = model_profile(model)
        return profile.status if profile else "unknown"

    def _gateway_status(self, model: str, gateway_compatibility: dict[str, Any]) -> str:
        canonical = canonical_model_id(model)
        for role in _list(gateway_compatibility.get("configured_roles")):
            if not isinstance(role, dict):
                continue
            if role.get("model") == model or role.get("canonical_model") == canonical:
                return str(role.get("status") or "unknown")
        profile = model_profile(model)
        if profile:
            return "pass"
        return "warn" if "gemini" in model.lower() else "fail"

    def _price_status(self, profile: Any) -> str:
        if profile is None:
            return "unknown"
        if profile.output_usd_per_image is not None:
            return "priced_per_image"
        if profile.input_usd_per_million_tokens is not None and profile.output_usd_per_million_tokens is not None:
            return "priced_per_token"
        return "missing"

    def _cheap_first_aligned(
        self,
        task: str,
        profile: Any,
        recommended_profile: Any,
        runtime_default: str,
        recommended: str,
    ) -> bool:
        if profile is None:
            return False
        if task in PREMIUM_EXCEPTION_TASKS:
            return profile.cost_tier == "premium" or self._price_status(profile) == "priced_per_image"
        if task in BALANCED_TASKS:
            return _tier_rank(profile.cost_tier) <= _tier_rank("medium")
        if task in CHEAP_FIRST_TASKS:
            if recommended_profile and runtime_default != recommended:
                return False
            return _tier_rank(profile.cost_tier) <= _tier_rank("low")
        return profile.family == "gemini"

    def _model_family(self, profile: Any, task: str) -> str:
        if profile is None:
            return "unknown"
        if task == "image":
            return "media"
        return str(profile.family or "unknown")

    def _reason_codes(
        self,
        *,
        task: str,
        runtime_profile: Any,
        recommended_profile: Any,
        runtime_default: str,
        recommended: str,
        lifecycle_status: str,
        price_status: str,
        reasoning_policy_status: str,
        gateway_status: str,
        cheap_first_aligned: bool,
        premium_exception: bool,
    ) -> list[str]:
        codes: list[str] = []
        if runtime_profile is None:
            codes.append("unknown_model")
        elif self._model_family(runtime_profile, task) not in {"gemini", "media"}:
            codes.append("non_gemini_default")
        if runtime_default != recommended and task in CHEAP_FIRST_TASKS:
            codes.append("runtime_default_not_cheapest_capable")
        if recommended_profile is None:
            codes.append("recommended_model_missing_catalog")
        if lifecycle_status != "stable":
            codes.append(f"lifecycle:{lifecycle_status}")
        if price_status in {"missing", "unknown"}:
            codes.append(f"price:{price_status}")
        if reasoning_policy_status != "ready" and not premium_exception:
            codes.append("reasoning_policy_missing")
        if gateway_status != "pass":
            codes.append(f"gateway:{gateway_status}")
        if not cheap_first_aligned:
            codes.append("cheap_first_not_aligned")
        if premium_exception:
            codes.append("premium_exception_requires_review")
        return codes or ["coverage_ready"]

    def _coverage_status(self, reason_codes: list[str], premium_exception: bool) -> str:
        blocking = {"unknown_model", "non_gemini_default", "cheap_first_not_aligned"}
        if any(code in blocking or code.startswith("gateway:fail") for code in reason_codes):
            return "blocked"
        if premium_exception or any(code != "coverage_ready" for code in reason_codes):
            return "review_required"
        return "ready"

    def _release_action(self, coverage_status: str, premium_exception: bool) -> str:
        if coverage_status == "ready":
            return "keep_cheap_first_default"
        if coverage_status == "blocked":
            return "block_default_promotion"
        if premium_exception:
            return "require_operator_premium_exception"
        return "maintainer_review_before_default_change"

    def _recommended_actions(self, blocked: list[dict[str, Any]], review: list[dict[str, Any]]) -> list[str]:
        if blocked:
            return [
                "Move blocked high-volume defaults back to known Gemini Flash-Lite or Flash catalog models before release.",
                "Add catalog pricing, lifecycle, reasoning, and gateway compatibility metadata before promoting unknown Gemini-like ids.",
                "Keep current default changes blocked until this coverage gate has no blocked rows.",
            ]
        if review:
            return [
                "Keep current cheap-first defaults while maintainer reviews premium exceptions, preview models, missing pricing, or gateway warnings.",
                "Use explicit request models for grounded research, agentic, PDF, and media exceptions until catalog evidence is complete.",
            ]
        return [
            "Keep Gemini cheap-first defaults and rerun this gate before every model catalog or environment default change.",
            "Use Flash-Lite for high-volume tasks, Flash for balanced review, and Pro/media models only as reviewed exceptions.",
        ]


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict_or(value: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    return value if isinstance(value, dict) else fallback


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)
