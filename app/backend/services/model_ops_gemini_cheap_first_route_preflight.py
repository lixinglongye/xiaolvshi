from __future__ import annotations

from typing import Any

from services.gemini_model_variant_matrix import GeminiModelVariantMatrixService
from services.gemini_newapi_alias_capability_coverage import GeminiNewapiAliasCapabilityCoverageService
from services.model_catalog import catalog_for_api, canonical_model_id, model_profile, task_default_model
from services.modelops_gemini_cheap_first_coverage_gate import ModelOpsGeminiCheapFirstCoverageGateService


HIGH_FREQUENCY_TASKS = ("fast", "routing", "classification", "ocr", "agentic", "grounded-research", "embedding")
BALANCED_TASKS = ("review", "document-generation")
PREMIUM_EXCEPTION_TASKS = ("pdf", "image")
ALL_ROUTE_TASKS = HIGH_FREQUENCY_TASKS + BALANCED_TASKS + PREMIUM_EXCEPTION_TASKS

OFFICIAL_SOURCE_ROWS = (
    {
        "id": "gemini-api-models",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "tracked_signal": "Gemini model family names, lifecycle status, modalities, and stable vs preview posture.",
        "refresh_action": "Recheck before adding new Gemini ids to the local default candidate list.",
    },
    {
        "id": "gemini-api-pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing",
        "tracked_signal": "Token and image pricing used to keep Flash-Lite ahead of Flash and Pro for high-volume tasks.",
        "refresh_action": "Recompute local cost tiers and route budgets before changing APP_AI_* defaults.",
    },
    {
        "id": "gemini-openai-compatible",
        "url": "https://ai.google.dev/gemini-api/docs/openai",
        "tracked_signal": "OpenAI-compatible request shapes and model ids that NewAPI-style gateways may expose.",
        "refresh_action": "Keep gateway-prefixed aliases explicit-only until they canonicalize to a catalog row.",
    },
    {
        "id": "vertex-ai-model-versions",
        "url": "https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions",
        "tracked_signal": "Published model version and retirement status for Gemini variants.",
        "refresh_action": "Block retired generations from default routing even if a gateway still accepts a legacy alias.",
    },
)


class ModelOpsGeminiCheapFirstRoutePreflightService:
    """Build metadata-only route preflight evidence for Gemini cheap-first defaults."""

    def __init__(
        self,
        *,
        variant_matrix_service: GeminiModelVariantMatrixService | None = None,
        alias_coverage_service: GeminiNewapiAliasCapabilityCoverageService | None = None,
        coverage_gate_service: ModelOpsGeminiCheapFirstCoverageGateService | None = None,
    ) -> None:
        self.variant_matrix_service = variant_matrix_service or GeminiModelVariantMatrixService()
        self.alias_coverage_service = alias_coverage_service or GeminiNewapiAliasCapabilityCoverageService()
        self.coverage_gate_service = coverage_gate_service or ModelOpsGeminiCheapFirstCoverageGateService()

    def build_preflight(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        observed_models = _list(data.get("observed_models"))
        variant_matrix = _dict_or(
            data.get("gemini_variant_matrix"),
            self.variant_matrix_service.build_matrix({"observed_models": observed_models}),
        )
        alias_coverage = _dict_or(
            data.get("gemini_newapi_alias_capability_coverage"),
            self.alias_coverage_service.build_coverage({"observed_models": observed_models}),
        )
        coverage_gate = _dict_or(
            data.get("gemini_cheap_first_coverage_gate"),
            self.coverage_gate_service.build_gate(),
        )
        route_rows = [self._route_row(task, coverage_gate, alias_coverage) for task in ALL_ROUTE_TASKS]
        variant_rows = self._variant_rows(variant_matrix, alias_coverage)
        checks = self._checks(route_rows, variant_rows, variant_matrix, alias_coverage, coverage_gate)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "pass")

        return {
            "id": "modelops-gemini-cheap-first-route-preflight",
            "title": "ModelOps Gemini cheap-first route preflight",
            "status": status,
            "method": {
                "type": "metadata-only-gemini-route-preflight",
                "notes": [
                    "Joins official source refresh notes, local Gemini catalog rows, alias capability coverage, and cheap-first coverage rows.",
                    "Keeps Flash-Lite first for high-volume tasks and requires review for Flash, Pro, image, preview, unknown, or unpriced variants.",
                    "Does not call NewAPI, Gemini, Google, OpenAI, gateways, app AI endpoints, or the network.",
                ],
            },
            "summary": {
                "official_source_count": len(OFFICIAL_SOURCE_ROWS),
                "catalog_model_count": len(catalog_for_api()),
                "route_task_count": len(route_rows),
                "cheap_first_route_count": sum(1 for row in route_rows if row["route_mode"] == "cheap_first"),
                "balanced_route_count": sum(1 for row in route_rows if row["route_mode"] == "cheap_precheck_then_balanced"),
                "premium_exception_count": sum(1 for row in route_rows if row["premium_exception_required"]),
                "variant_row_count": len(variant_rows),
                "default_allowed_variant_count": sum(1 for row in variant_rows if row["default_allowed_without_review"]),
                "review_variant_count": sum(1 for row in variant_rows if row["default_promotion_state"] == "review_required"),
                "blocked_variant_count": sum(1 for row in variant_rows if row["default_promotion_state"] == "blocked"),
                "observed_model_count": int(_summary_value(variant_matrix, "observed_model_count")),
                "alias_shape_count": int(_summary_value(alias_coverage, "alias_shape_count")),
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "credentials_included": False,
                "raw_payload_echoed": False,
            },
            "official_source_rows": [dict(row) for row in OFFICIAL_SOURCE_ROWS],
            "route_task_rows": route_rows,
            "variant_preflight_rows": variant_rows,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "recommended_actions": self._recommended_actions(blocking, warnings),
            "source_signal_summary": {
                "gemini_variant_matrix_status": str(variant_matrix.get("status") or "unknown"),
                "gemini_alias_capability_status": str(alias_coverage.get("status") or "unknown"),
                "gemini_cheap_first_coverage_status": str(coverage_gate.get("status") or "unknown"),
                "variant_matrix_validation_commands": _list(variant_matrix.get("validation_commands"))[:3],
                "alias_coverage_validation_commands": _list(alias_coverage.get("validation_commands"))[:3],
                "coverage_gate_validation_commands": _list(coverage_gate.get("validation_commands"))[:3],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "returns_credentials": False,
                "returns_api_key": False,
                "returns_headers": False,
                "returns_request_body": False,
                "returns_response_body": False,
                "returns_raw_prompt": False,
                "returns_raw_payload": False,
                "returns_raw_model_output": False,
                "returns_raw_legal_text": False,
                "output_scope": "official-source ids and URLs, model ids, task labels, cost tiers, route modes, checks, and validation commands only",
            },
            "claim_boundary": {
                "official_refresh_completed": False,
                "live_gateway_execution_claimed": False,
                "automatic_default_change_claimed": False,
                "production_quality_claimed": False,
                "public_benchmark_score_claimed": False,
                "allowed_claim": "The repository exposes metadata-only preflight evidence for Gemini cheap-first route review.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_cheap_first_route_preflight.py tests/test_model_ops_readiness.py -q",
                "python -m pytest tests/test_gemini_model_variant_matrix.py tests/test_gemini_newapi_alias_capability_coverage.py tests/test_modelops_gemini_cheap_first_coverage_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _route_row(
        self,
        task: str,
        coverage_gate: dict[str, Any],
        alias_coverage: dict[str, Any],
    ) -> dict[str, Any]:
        default_model = task_default_model(task)
        canonical = canonical_model_id(default_model)
        profile = model_profile(default_model)
        coverage_row = _find_by(coverage_gate.get("coverage_rows"), "task", task)
        alias_task = _find_by(alias_coverage.get("task_alias_coverage"), "task", task)
        route_mode = self._route_mode(task)
        premium_exception = task in PREMIUM_EXCEPTION_TASKS
        reason_codes = self._route_reason_codes(task, profile, coverage_row, alias_task, premium_exception)
        cheap_first_aligned = (
            bool(profile)
            and task in HIGH_FREQUENCY_TASKS
            and "flash-lite" in (canonical or "")
        ) or bool(coverage_row.get("cheap_first_aligned"))
        return {
            "id": f"gemini-route-preflight-{task}",
            "task": task,
            "route_mode": route_mode,
            "default_model": default_model,
            "canonical_model": canonical,
            "model_status": profile.status if profile else "unknown",
            "cost_tier": profile.cost_tier if profile else "unknown",
            "capabilities": list(profile.capabilities) if profile else [],
            "high_frequency_task": task in HIGH_FREQUENCY_TASKS,
            "cheap_first_required": task in HIGH_FREQUENCY_TASKS,
            "cheap_first_aligned": cheap_first_aligned,
            "premium_exception_required": premium_exception,
            "default_allowed_without_review": not premium_exception
            and not reason_codes
            and profile is not None
            and profile.status == "stable",
            "alias_coverage_status": str(alias_task.get("status") or "unknown") if alias_task else "unknown",
            "coverage_status": str(coverage_row.get("coverage_status") or "unknown") if coverage_row else "unknown",
            "release_action": self._release_action(reason_codes, premium_exception),
            "reason_codes": reason_codes or ["route_preflight_ready"],
            "next_action": self._route_action(reason_codes, premium_exception),
        }

    def _variant_rows(self, variant_matrix: dict[str, Any], alias_coverage: dict[str, Any]) -> list[dict[str, Any]]:
        alias_by_canonical: dict[str, list[str]] = {}
        for row in _list_dicts(alias_coverage.get("coverage_rows")):
            canonical = str(row.get("canonical_model") or row.get("alias_model") or "")
            if not canonical:
                continue
            alias_by_canonical.setdefault(canonical, []).append(str(row.get("alias_model") or canonical))

        rows: list[dict[str, Any]] = []
        for row in _list_dicts(variant_matrix.get("model_rows")):
            model_id = str(row.get("model_id") or "")
            route_role = str(row.get("route_role") or "explicit_only")
            catalog_status = str(row.get("catalog_status") or "unknown")
            cost_tier = str(row.get("cost_tier") or "unknown")
            pricing_status = str(row.get("pricing_status") or "unknown")
            reason_codes = self._variant_reason_codes(row)
            rows.append(
                {
                    "model_id": model_id,
                    "family": str(row.get("family") or "unknown"),
                    "catalog_status": catalog_status,
                    "cost_tier": cost_tier,
                    "pricing_status": pricing_status,
                    "route_role": route_role,
                    "high_frequency_default_allowed": bool(row.get("high_frequency_default_allowed")),
                    "balanced_retry_allowed": bool(row.get("balanced_retry_allowed")),
                    "premium_exception_required": bool(row.get("premium_exception_required")),
                    "media_route_only": bool(row.get("media_route_only")),
                    "default_allowed_without_review": bool(row.get("high_frequency_default_allowed"))
                    and not reason_codes,
                    "default_promotion_state": self._variant_state(reason_codes, route_role),
                    "accepted_alias_examples": sorted(set(alias_by_canonical.get(model_id, [])))[:6],
                    "supported_request_shapes": _list(row.get("supported_request_shapes"))[:4],
                    "reason_codes": reason_codes or ["variant_preflight_ready"],
                    "recommended_action": self._variant_action(reason_codes, route_role),
                }
            )
        return rows

    def _checks(
        self,
        route_rows: list[dict[str, Any]],
        variant_rows: list[dict[str, Any]],
        variant_matrix: dict[str, Any],
        alias_coverage: dict[str, Any],
        coverage_gate: dict[str, Any],
    ) -> list[dict[str, Any]]:
        high_frequency_failures = [
            row["task"]
            for row in route_rows
            if row["high_frequency_task"] and not row["cheap_first_aligned"]
        ]
        unknown_defaults = [
            row["task"]
            for row in route_rows
            if "unknown_model" in row["reason_codes"] or row["model_status"] == "unknown"
        ]
        review_variants = [
            row["model_id"]
            for row in variant_rows
            if row["default_promotion_state"] == "review_required"
        ]
        blocked_variants = [
            row["model_id"]
            for row in variant_rows
            if row["default_promotion_state"] == "blocked" and row["default_allowed_without_review"]
        ]
        alias_shapes = int(_summary_value(alias_coverage, "alias_shape_count"))
        checks = [
            self._check(
                "high-frequency-flash-lite-defaults",
                "fail" if high_frequency_failures else "pass",
                "High-frequency text tasks keep a Flash-Lite default, while embedding tasks keep a lowest-tier embedding default.",
                high_frequency_failures,
            ),
            self._check(
                "known-default-models",
                "fail" if unknown_defaults else "pass",
                "Every default model resolves to the local Gemini catalog.",
                unknown_defaults,
            ),
            self._check(
                "gateway-alias-coverage-present",
                "pass" if alias_shapes >= len(catalog_for_api()) else "warn",
                "NewAPI/OpenAI-compatible alias shapes are represented before gateway use.",
                [str(alias_shapes)],
            ),
            self._check(
                "preview-premium-review-boundary",
                "warn" if review_variants else "pass",
                "Preview, Pro, image, unknown, and unpriced variants stay review-only.",
                review_variants,
            ),
            self._check(
                "blocked-variant-boundary",
                "fail" if blocked_variants else "pass",
                "No blocked Gemini variant is allowed into default-promotion candidates.",
                blocked_variants,
            ),
            self._check(
                "source-signal-status",
                "pass"
                if all(
                    str(item.get("status") or "") in {"pass", "ready", "review_required", "monitor_only"}
                    for item in (variant_matrix, alias_coverage, coverage_gate)
                )
                else "warn",
                "Upstream ModelOps signals are present and reviewable.",
                [
                    f"variant={variant_matrix.get('status', 'unknown')}",
                    f"alias={alias_coverage.get('status', 'unknown')}",
                    f"coverage={coverage_gate.get('status', 'unknown')}",
                ],
            ),
            self._check(
                "metadata-only-boundary",
                "pass",
                "Preflight output is metadata-only and never calls or writes provider configuration.",
                ["model_called:false", "gateway_called:false", "configuration_written:false"],
            ),
        ]
        return checks

    def _check(self, check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
        return {
            "id": check_id,
            "status": status,
            "reason": reason,
            "evidence": evidence[:8],
        }

    def _route_reason_codes(
        self,
        task: str,
        profile: Any,
        coverage_row: dict[str, Any],
        alias_task: dict[str, Any],
        premium_exception: bool,
    ) -> list[str]:
        codes: list[str] = []
        if profile is None:
            codes.append("unknown_model")
        else:
            if task == "embedding":
                if "embedding" not in set(profile.capabilities):
                    codes.append("high_frequency_embedding_capability_missing")
                if profile.cost_tier != "lowest":
                    codes.append("embedding_cost_review")
            elif task in HIGH_FREQUENCY_TASKS and "flash-lite" not in profile.id:
                codes.append("high_frequency_not_flash_lite")
            if profile.status != "stable":
                codes.append(f"lifecycle_{profile.status}")
            if profile.cost_tier in {"premium", "unknown"} and task in HIGH_FREQUENCY_TASKS:
                codes.append("high_frequency_cost_review")
        if coverage_row and coverage_row.get("coverage_status") not in {"ready", "review_required"}:
            codes.append(f"coverage_{coverage_row.get('coverage_status')}")
        if alias_task and alias_task.get("status") not in {"covered", "pass", "ready"}:
            codes.append("alias_task_review")
        if premium_exception:
            codes.append("premium_exception_review")
        return codes

    def _variant_reason_codes(self, row: dict[str, Any]) -> list[str]:
        codes: list[str] = []
        model_id = str(row.get("model_id") or "")
        status = str(row.get("catalog_status") or "unknown")
        pricing = str(row.get("pricing_status") or "unknown")
        route_role = str(row.get("route_role") or "")
        if status != "stable":
            codes.append(f"lifecycle_{status}")
        if pricing == "unpriced":
            codes.append("pricing_missing")
        if row.get("premium_exception_required") or str(row.get("cost_tier") or "") == "premium":
            codes.append("premium_exception_review")
        if row.get("media_route_only"):
            codes.append("media_route_review")
        if route_role == "explicit_only":
            codes.append("explicit_only")
        if model_id.startswith("gemini-2.0") or model_id.startswith("gemini-1."):
            codes.append("retired_generation")
        return codes

    def _variant_state(self, reason_codes: list[str], route_role: str) -> str:
        if "retired_generation" in reason_codes or "pricing_missing" in reason_codes:
            return "blocked"
        if route_role == "cheap_first_default" and not reason_codes:
            return "ready"
        if reason_codes:
            return "review_required"
        return "review_required"

    def _variant_action(self, reason_codes: list[str], route_role: str) -> str:
        if "retired_generation" in reason_codes:
            return "Remove the retired generation from default candidates and keep it explicit-only if a gateway still exposes it."
        if "pricing_missing" in reason_codes:
            return "Add pricing evidence before the variant can be used in cost forecasts or default routing."
        if route_role == "cheap_first_default" and not reason_codes:
            return "Keep this Flash-Lite variant as a high-volume default candidate after gateway alias support is confirmed."
        if "premium_exception_review" in reason_codes:
            return "Require operator review and release evidence before this premium variant is used outside explicit requests."
        if "media_route_review" in reason_codes:
            return "Keep this model on explicit media routes and out of text default cascades."
        return "Keep explicit-only until lifecycle, capability, pricing, and gateway support are reviewed."

    def _route_mode(self, task: str) -> str:
        if task in HIGH_FREQUENCY_TASKS:
            return "cheap_first"
        if task in BALANCED_TASKS:
            return "cheap_precheck_then_balanced"
        return "operator_reviewed_exception"

    def _release_action(self, reason_codes: list[str], premium_exception: bool) -> str:
        if "unknown_model" in reason_codes:
            return "block_default_route"
        if premium_exception:
            return "require_operator_exception"
        if reason_codes:
            return "maintainer_review"
        return "keep_default_route"

    def _route_action(self, reason_codes: list[str], premium_exception: bool) -> str:
        if "unknown_model" in reason_codes:
            return "Pin this task to a known Gemini catalog id before route promotion."
        if premium_exception:
            return "Keep explicit operator approval for this task and record benchmark or user-need evidence before use."
        if reason_codes:
            return "Review lifecycle, cost, alias coverage, and quality gates before changing this task default."
        return "Keep the current cheap-first route and rerun this preflight before default changes."

    def _recommended_actions(self, blocking: list[str], warnings: list[str]) -> list[str]:
        if blocking:
            return [
                "Do not promote any Gemini default change while route preflight has blocking checks.",
                "Resolve unknown, retired, unpriced, or blocked variants before modifying APP_AI_* defaults.",
            ]
        if warnings:
            return [
                "Keep Flash-Lite as the first high-volume default while maintainers review premium, preview, media, or alias coverage warnings.",
                "Refresh official Gemini model and pricing pages before accepting new observed gateway ids.",
            ]
        return [
            "Keep the current Gemini cheap-first route plan and rerun preflight before every catalog, alias, or default-model change.",
            "Use Flash-Lite for high-volume tasks, Flash after deterministic precheck, and Pro/media only as explicit reviewed exceptions.",
        ]


def _dict_or(value: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    return value if isinstance(value, dict) else fallback


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _list_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _find_by(value: Any, key: str, needle: str) -> dict[str, Any]:
    for item in _list_dicts(value):
        if str(item.get(key) or "") == needle:
            return item
    return {}


def _summary_value(value: dict[str, Any], key: str) -> int:
    summary = value.get("summary") if isinstance(value.get("summary"), dict) else {}
    raw = summary.get(key, 0)
    return raw if isinstance(raw, int) else 0
