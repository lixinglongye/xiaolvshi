from __future__ import annotations

from typing import Any

from services.model_ops_gemini_cheap_first_route_preflight import (
    ModelOpsGeminiCheapFirstRoutePreflightService,
)
from services.model_ops_legal_benchmark_risk_bridge import ModelOpsLegalBenchmarkRiskBridgeService
from services.modelops_legal_micro_benchmark_preflight import ModelOpsLegalMicroBenchmarkPreflightService


RESEARCH_SOURCE_ROWS = (
    {
        "id": "gemini-api-models",
        "source_type": "official_model_catalog",
        "title": "Gemini API model catalog",
        "url": "https://ai.google.dev/gemini-api/docs/models",
        "tracked_signal": "Gemini family names, supported modalities, lifecycle status, and preview posture.",
        "refresh_cadence": "before_default_model_change",
        "default_decision_use": "Block unknown or retired Gemini variants from automatic defaults.",
    },
    {
        "id": "gemini-api-pricing",
        "source_type": "official_pricing",
        "title": "Gemini API pricing",
        "url": "https://ai.google.dev/gemini-api/docs/pricing",
        "tracked_signal": "Flash-Lite, Flash, Pro, image, embedding, and batch price tiers.",
        "refresh_cadence": "before_budget_or_cost_tier_change",
        "default_decision_use": "Keep high-volume routes cheap-first unless price evidence supports a change.",
    },
    {
        "id": "gemini-openai-compatible",
        "source_type": "official_gateway_compatibility",
        "title": "Gemini OpenAI-compatible interface",
        "url": "https://ai.google.dev/gemini-api/docs/openai",
        "tracked_signal": "OpenAI-compatible endpoint and model-id shapes exposed by Gemini-compatible gateways.",
        "refresh_cadence": "before_gateway_alias_acceptance",
        "default_decision_use": "Treat new gateway aliases as explicit-only until canonical catalog fit is reviewed.",
    },
    {
        "id": "legalbench",
        "source_type": "public_legal_benchmark",
        "title": "LegalBench legal reasoning benchmark",
        "url": "https://github.com/HazyResearch/legalbench",
        "tracked_signal": "Legal task categories and benchmark-style evaluation coverage.",
        "refresh_cadence": "before_claiming_public_benchmark_alignment",
        "default_decision_use": "Map user-facing legal tasks to benchmark categories before route promotion.",
    },
    {
        "id": "cuad",
        "source_type": "public_contract_dataset",
        "title": "CUAD contract understanding dataset",
        "url": "https://www.atticusprojectai.org/cuad",
        "tracked_signal": "Contract-review clause extraction and attorney-reviewed document understanding coverage.",
        "refresh_cadence": "before_contract_review_default_change",
        "default_decision_use": "Keep contract extraction defaults gated by fixture and license review evidence.",
    },
)

ADOPTION_TASK_TARGETS = (
    {
        "id": "cheap-fast-review",
        "task": "fast",
        "product_area": "high_frequency_triage",
        "required_source_ids": ("gemini-api-models", "gemini-api-pricing", "legalbench"),
        "benchmark_requirement": "legal reasoning smoke fixtures before changing fast default",
        "route_mode": "cheap_first",
    },
    {
        "id": "ocr-contract-intake",
        "task": "ocr",
        "product_area": "document_intake",
        "required_source_ids": ("gemini-api-models", "gemini-api-pricing", "cuad"),
        "benchmark_requirement": "contract clause and evidence extraction fixtures before OCR promotion",
        "route_mode": "cheap_first",
    },
    {
        "id": "legal-review-balanced",
        "task": "review",
        "product_area": "deep_legal_review",
        "required_source_ids": ("gemini-api-models", "gemini-api-pricing", "legalbench", "cuad"),
        "benchmark_requirement": "cheap precheck plus balanced review fixtures before any default change",
        "route_mode": "cheap_precheck_then_balanced",
    },
    {
        "id": "pdf-contract-review",
        "task": "pdf",
        "product_area": "large_document_review",
        "required_source_ids": ("gemini-api-models", "gemini-api-pricing", "cuad"),
        "benchmark_requirement": "operator-reviewed exception evidence for PDF-heavy contract review",
        "route_mode": "operator_reviewed_exception",
    },
    {
        "id": "grounded-research",
        "task": "grounded-research",
        "product_area": "source_grounded_research",
        "required_source_ids": ("gemini-api-models", "gemini-api-pricing", "legalbench"),
        "benchmark_requirement": "source-grounded answer fixtures and abstention checks before route promotion",
        "route_mode": "cheap_first",
    },
)


class ModelOpsGeminiResearchRefreshGateService:
    """Join official Gemini and legal benchmark research signals into a cheap-first review gate."""

    def __init__(
        self,
        route_preflight_service: ModelOpsGeminiCheapFirstRoutePreflightService | None = None,
        legal_micro_benchmark_service: ModelOpsLegalMicroBenchmarkPreflightService | None = None,
        legal_risk_bridge_service: ModelOpsLegalBenchmarkRiskBridgeService | None = None,
    ) -> None:
        self.route_preflight_service = route_preflight_service or ModelOpsGeminiCheapFirstRoutePreflightService()
        self.legal_micro_benchmark_service = (
            legal_micro_benchmark_service or ModelOpsLegalMicroBenchmarkPreflightService()
        )
        self.legal_risk_bridge_service = legal_risk_bridge_service or ModelOpsLegalBenchmarkRiskBridgeService()

    def build_gate(self, signals: dict[str, Any] | None = None) -> dict[str, Any]:
        data = signals if isinstance(signals, dict) else {}
        route_preflight = _dict_or(
            data.get("gemini_cheap_first_route_preflight"),
            self.route_preflight_service.build_preflight(data),
        )
        legal_micro_benchmark = _dict_or(
            data.get("legal_micro_benchmark_preflight"),
            self.legal_micro_benchmark_service.build_packet(),
        )
        legal_risk_bridge = _dict_or(
            data.get("legal_benchmark_risk_bridge"),
            self.legal_risk_bridge_service.build_bridge(data),
        )
        source_rows = [dict(row) for row in RESEARCH_SOURCE_ROWS]
        adoption_rows = [
            self._adoption_row(target, source_rows, route_preflight, legal_micro_benchmark, legal_risk_bridge)
            for target in ADOPTION_TASK_TARGETS
        ]
        checks = self._checks(source_rows, adoption_rows, route_preflight, legal_micro_benchmark, legal_risk_bridge)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]

        return {
            "id": "modelops-gemini-research-refresh-gate",
            "title": "ModelOps Gemini research refresh gate",
            "status": "blocked" if blocking else ("review_required" if warnings else "ready"),
            "method": {
                "type": "metadata-only-gemini-research-refresh-gate",
                "notes": [
                    "Joins official Gemini source rows, public legal benchmark source rows, route preflight, and micro-benchmark evidence.",
                    "Keeps Flash-Lite cheap-first defaults separate from balanced, Pro, PDF, image, and external benchmark review claims.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, benchmark repositories, app AI endpoints, or the network.",
                ],
            },
            "summary": {
                "research_source_count": len(source_rows),
                "official_source_count": sum(1 for row in source_rows if row["source_type"].startswith("official")),
                "public_benchmark_source_count": sum(
                    1 for row in source_rows if row["source_type"].startswith("public")
                ),
                "adoption_task_count": len(adoption_rows),
                "ready_adoption_count": sum(1 for row in adoption_rows if row["adoption_status"] == "ready"),
                "review_adoption_count": sum(
                    1 for row in adoption_rows if row["adoption_status"] == "review_required"
                ),
                "blocked_adoption_count": sum(1 for row in adoption_rows if row["adoption_status"] == "blocked"),
                "cheap_first_task_count": sum(1 for row in adoption_rows if row["route_mode"] == "cheap_first"),
                "public_benchmark_license_review_count": sum(
                    1 for row in adoption_rows if row["license_review_required"]
                ),
                "external_refresh_completed": False,
                "public_benchmark_downloaded": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "raw_payload_echoed": False,
            },
            "research_source_rows": source_rows,
            "adoption_rows": adoption_rows,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "source_signal_summary": {
                "gemini_cheap_first_route_preflight_status": str(route_preflight.get("status") or "missing"),
                "legal_micro_benchmark_preflight_status": str(legal_micro_benchmark.get("status") or "missing"),
                "legal_benchmark_risk_bridge_status": str(legal_risk_bridge.get("status") or "missing"),
                "route_preflight_warning_count": len(_list(route_preflight.get("warning_check_ids"))),
                "legal_micro_blocking_count": len(_list(legal_micro_benchmark.get("blocking_check_ids"))),
                "legal_risk_bridge_warning_count": len(_list(legal_risk_bridge.get("warning_check_ids"))),
            },
            "refresh_policy": {
                "external_source_refresh_required_before_default_change": True,
                "public_benchmark_license_review_required": True,
                "cheap_first_defaults_require_lowest_cost_source_evidence": True,
                "benchmark_scores_must_be_fixture_backed": True,
                "automatic_default_change_allowed": False,
                "network_refresh_allowed_by_this_gate": False,
                "configuration_write_allowed": False,
            },
            "recommended_actions": self._recommended_actions(blocking, warnings, adoption_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_source_urls": True,
                "returns_route_task_ids": True,
                "returns_benchmark_samples": False,
                "returns_public_dataset_rows": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "output_scope": "source ids, URLs, task ids, route modes, benchmark requirements, statuses, and validation commands only",
            },
            "claim_boundary": {
                "official_refresh_completed": False,
                "public_benchmark_scores_claimed": False,
                "external_dataset_execution_claimed": False,
                "live_gateway_quality_claimed": False,
                "default_model_changed": False,
                "routing_change_applied": False,
                "all_gemini_models_supported_claimed": False,
                "allowed_claim": "The repository exposes metadata-only research refresh evidence for Gemini cheap-first route reviews.",
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_gemini_research_refresh_gate.py tests/test_model_ops_gemini_cheap_first_route_preflight.py tests/test_modelops_legal_micro_benchmark_preflight.py -q",
                "python -m pytest tests/test_model_ops_readiness.py tests/test_model_ops_legal_benchmark_risk_bridge.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _adoption_row(
        self,
        target: dict[str, Any],
        source_rows: list[dict[str, Any]],
        route_preflight: dict[str, Any],
        legal_micro_benchmark: dict[str, Any],
        legal_risk_bridge: dict[str, Any],
    ) -> dict[str, Any]:
        task = str(target["task"])
        route_row = _find_by(route_preflight.get("route_task_rows"), "task", task)
        required_source_ids = _string_list(target.get("required_source_ids"))
        missing_source_ids = [
            source_id
            for source_id in required_source_ids
            if not any(row["id"] == source_id for row in source_rows)
        ]
        legal_route_review = _find_legal_route_review(legal_risk_bridge, task)
        route_reason_codes = _string_list(route_row.get("reason_codes"))
        legal_reason_codes = _string_list(legal_route_review.get("reason_codes"))
        reason_codes = self._adoption_reason_codes(
            missing_source_ids,
            route_row,
            route_reason_codes,
            legal_micro_benchmark,
            legal_route_review,
            legal_reason_codes,
        )
        return {
            "id": f"gemini-research-refresh-{target['id']}",
            "task": task,
            "product_area": target["product_area"],
            "route_mode": target["route_mode"],
            "default_model": str(route_row.get("default_model") or "unknown"),
            "canonical_model": route_row.get("canonical_model"),
            "cost_tier": str(route_row.get("cost_tier") or "unknown"),
            "cheap_first_aligned": bool(route_row.get("cheap_first_aligned")),
            "required_source_ids": required_source_ids,
            "missing_source_ids": missing_source_ids,
            "benchmark_requirement": target["benchmark_requirement"],
            "legal_micro_benchmark_status": str(legal_micro_benchmark.get("status") or "missing"),
            "legal_risk_level": str(legal_route_review.get("risk_level") or "unmapped"),
            "license_review_required": "cuad" in required_source_ids or "legalbench" in required_source_ids,
            "adoption_status": self._adoption_status(reason_codes, route_row, legal_route_review),
            "release_action": self._release_action(reason_codes),
            "reason_codes": reason_codes or ["research_refresh_ready"],
            "next_action": self._next_action(reason_codes, task),
            "network_called": False,
            "configuration_written": False,
        }

    def _adoption_reason_codes(
        self,
        missing_source_ids: list[str],
        route_row: dict[str, Any],
        route_reason_codes: list[str],
        legal_micro_benchmark: dict[str, Any],
        legal_route_review: dict[str, Any],
        legal_reason_codes: list[str],
    ) -> list[str]:
        codes: list[str] = []
        if missing_source_ids:
            codes.append("research_source_missing")
        if not route_row:
            codes.append("route_preflight_missing")
        if route_row and not route_row.get("cheap_first_aligned") and route_row.get("route_mode") == "cheap_first":
            codes.append("cheap_first_alignment_review")
        if any(code.startswith("premium_exception") or code == "unknown_model" for code in route_reason_codes):
            codes.append("route_exception_review")
        if str(legal_micro_benchmark.get("status") or "") not in {"ready", "review_required"}:
            codes.append("legal_micro_benchmark_not_ready")
        if not legal_route_review:
            codes.append("legal_benchmark_route_unmapped")
        elif legal_route_review.get("risk_level") in {"block", "operator_exception"}:
            codes.append(f"legal_benchmark_{legal_route_review.get('risk_level')}")
        if "benchmark-license-review" in legal_reason_codes:
            codes.append("public_benchmark_license_review")
        return _dedupe(codes)

    def _adoption_status(
        self,
        reason_codes: list[str],
        route_row: dict[str, Any],
        legal_route_review: dict[str, Any],
    ) -> str:
        if any(code in {"research_source_missing", "route_preflight_missing", "legal_micro_benchmark_not_ready"} for code in reason_codes):
            return "blocked"
        if not route_row:
            return "blocked"
        if legal_route_review.get("risk_level") == "block":
            return "blocked"
        if reason_codes or not route_row.get("default_allowed_without_review"):
            return "review_required"
        return "ready"

    def _release_action(self, reason_codes: list[str]) -> str:
        if any(code.endswith("_missing") or code.endswith("_not_ready") for code in reason_codes):
            return "block_default_change"
        if reason_codes:
            return "maintainer_review"
        return "keep_current_route"

    def _next_action(self, reason_codes: list[str], task: str) -> str:
        if "research_source_missing" in reason_codes:
            return "Add the missing research source row before reviewing this task for route changes."
        if "route_preflight_missing" in reason_codes:
            return "Attach Gemini cheap-first route preflight evidence before research review."
        if "legal_micro_benchmark_not_ready" in reason_codes:
            return "Repair the local legal micro-benchmark preflight before changing legal route defaults."
        if "public_benchmark_license_review" in reason_codes:
            return "Keep benchmark mappings metadata-only until license review passes."
        if reason_codes:
            return f"Review route, benchmark, and source evidence before changing the {task} default."
        return f"Keep the current {task} route and refresh research sources before future default changes."

    def _checks(
        self,
        source_rows: list[dict[str, Any]],
        adoption_rows: list[dict[str, Any]],
        route_preflight: dict[str, Any],
        legal_micro_benchmark: dict[str, Any],
        legal_risk_bridge: dict[str, Any],
    ) -> list[dict[str, Any]]:
        missing_required_source_rows = [
            row["id"]
            for row in adoption_rows
            if row["missing_source_ids"]
        ]
        blocked_rows = [row["id"] for row in adoption_rows if row["adoption_status"] == "blocked"]
        review_rows = [row["id"] for row in adoption_rows if row["adoption_status"] == "review_required"]
        return [
            self._check(
                "official-gemini-sources-present",
                "pass" if sum(1 for row in source_rows if row["source_type"].startswith("official")) >= 3 else "fail",
                "Official Gemini model, pricing, and compatibility source rows are present.",
                [row["id"] for row in source_rows if row["source_type"].startswith("official")],
            ),
            self._check(
                "public-legal-benchmark-sources-present",
                "pass" if sum(1 for row in source_rows if row["source_type"].startswith("public")) >= 2 else "fail",
                "Public legal benchmark source rows are present for metadata-only review mapping.",
                [row["id"] for row in source_rows if row["source_type"].startswith("public")],
            ),
            self._check(
                "adoption-source-coverage",
                "fail" if missing_required_source_rows else "pass",
                "Every adoption task links to required Gemini and legal benchmark source rows.",
                missing_required_source_rows,
            ),
            self._check(
                "route-preflight-linked",
                "pass" if route_preflight.get("id") == "modelops-gemini-cheap-first-route-preflight" else "fail",
                "Gemini cheap-first route preflight is linked.",
                [str(route_preflight.get("status") or "missing")],
            ),
            self._check(
                "legal-micro-benchmark-linked",
                "pass" if legal_micro_benchmark.get("id") == "modelops-legal-micro-benchmark-preflight" else "fail",
                "Local legal micro-benchmark preflight is linked.",
                [str(legal_micro_benchmark.get("status") or "missing")],
            ),
            self._check(
                "legal-risk-bridge-linked",
                "pass" if legal_risk_bridge.get("id") == "modelops-legal-benchmark-risk-bridge" else "warn",
                "Legal benchmark risk bridge is linked for route review.",
                [str(legal_risk_bridge.get("status") or "missing")],
            ),
            self._check(
                "adoption-review-boundary",
                "fail" if blocked_rows else ("warn" if review_rows else "pass"),
                "Adoption rows stay blocked or review-only until research, benchmark, and route evidence is sufficient.",
                blocked_rows + review_rows,
            ),
            self._check(
                "metadata-only-boundary",
                "pass",
                "Research refresh output contains metadata only and never calls providers or downloads benchmarks.",
                ["network_called:false", "gateway_called:false", "configuration_written:false"],
            ),
        ]

    def _check(self, check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
        return {
            "id": check_id,
            "status": status,
            "reason": reason,
            "evidence": evidence[:8],
        }

    def _recommended_actions(
        self,
        blocking: list[str],
        warnings: list[str],
        adoption_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [
                "Do not change Gemini defaults while the research refresh gate has blocking checks.",
                "Attach route preflight, local legal micro-benchmark, and source rows before default promotion review.",
            ]
        actions = [
            "Keep current cheap-first Gemini defaults while maintainers refresh official source and legal benchmark mappings.",
            "Review public benchmark license boundaries before using LegalBench or CUAD mappings in promotion evidence.",
        ]
        if warnings:
            review_tasks = [row["task"] for row in adoption_rows if row["adoption_status"] == "review_required"][:5]
            if review_tasks:
                actions.append("Review adoption tasks before default changes: " + ", ".join(review_tasks) + ".")
        return actions


def _dict_or(value: Any, fallback: dict[str, Any]) -> dict[str, Any]:
    return value if isinstance(value, dict) else fallback


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    return [str(item) for item in _list(value) if str(item).strip()]


def _find_by(value: Any, key: str, needle: str) -> dict[str, Any]:
    for item in _list_of_dicts(value):
        if str(item.get(key) or "") == needle:
            return item
    return {}


def _find_legal_route_review(legal_risk_bridge: dict[str, Any], task: str) -> dict[str, Any]:
    for row in _list_of_dicts(legal_risk_bridge.get("route_reviews")):
        if str(row.get("task_id") or "") == task or str(row.get("task") or "") == task:
            return row
    return {}


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
