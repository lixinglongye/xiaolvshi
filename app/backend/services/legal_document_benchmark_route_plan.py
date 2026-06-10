from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.gemini_newapi_observed_model_extraction import safe_model_id
from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.model_catalog import estimate_token_cost_usd, model_profile
from services.model_default_candidate_selector import ModelDefaultCandidateSelectorService
from services.model_runtime_router import resolve_runtime_model


PLAN_ID = "legal-document-benchmark-cheap-first-route-plan"
PRECHECK_TASKS = ("classification", "fast")
PRECHECK_PROMPT_TOKENS = 1_600
PRECHECK_COMPLETION_TOKENS = 384
PRIMARY_PROMPT_TOKENS = {
    "classification": 2_000,
    "review": 12_000,
    "document-generation": 14_000,
    "grounded-research": 14_000,
}
PRIMARY_COMPLETION_TOKENS = {
    "classification": 512,
    "review": 2_048,
    "document-generation": 3_072,
    "grounded-research": 2_048,
}
DOCUMENT_PRIMARY_TASKS = {
    "civil_complaint": "document-generation",
    "defense_answer": "document-generation",
    "lawyer_letter": "document-generation",
    "contract_review": "review",
    "evidence_catalog": "classification",
    "settlement_agreement": "document-generation",
    "legal_opinion": "grounded-research",
}
PREMIUM_COST_TIERS = {"premium"}


@dataclass(frozen=True)
class RouteOverride:
    primary_task: str | None = None
    primary_model: str | None = None
    allow_over_budget_model: bool = False


class LegalDocumentBenchmarkRoutePlanService:
    """Plan cheap-first Gemini routes for small legal-document benchmark cases."""

    def __init__(
        self,
        suite_service: LegalDocumentBenchmarkSuiteService | None = None,
        coverage_service: LegalDocumentBenchmarkCoverageService | None = None,
        candidate_selector: ModelDefaultCandidateSelectorService | None = None,
    ) -> None:
        self.suite_service = suite_service or LegalDocumentBenchmarkSuiteService()
        self.coverage_service = coverage_service or LegalDocumentBenchmarkCoverageService()
        self.candidate_selector = candidate_selector or ModelDefaultCandidateSelectorService()

    def build_plan(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        suite = self.suite_service.build_suite()
        coverage = self.coverage_service.build_matrix()
        overrides = self._route_overrides(data.get("case_route_overrides"))
        case_rows = [self._case_route_row(case, overrides.get(case["id"])) for case in suite["benchmark_cases"]]
        checks = self._checks(case_rows, suite, coverage)
        blocking_check_ids = [check["id"] for check in checks if check["status"] == "fail"]
        warning_check_ids = [check["id"] for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking_check_ids else "ready_with_review" if warning_check_ids else "ready"
        premium_rows = [row for row in case_rows if row["primary_route"]["cost_tier"] in PREMIUM_COST_TIERS]
        routed_rows = [row for row in case_rows if row["primary_route"]["routed_to_recommended_model"]]
        estimated_precheck_cost = sum(row["estimated_precheck_cost_usd"] or 0.0 for row in case_rows)
        estimated_primary_cost = sum(row["estimated_primary_cost_usd"] or 0.0 for row in case_rows)

        return {
            "id": PLAN_ID,
            "status": status,
            "method": {
                "type": PLAN_ID,
                "version": "2026-06-10",
                "inputs": [
                    "legal_document_benchmark_suite benchmark case metadata",
                    "legal_document_benchmark_coverage coverage status",
                    "model_runtime_router budget decisions",
                    "model_default_candidate_selector cheap-first ladders",
                ],
                "notes": [
                    "Every benchmark case starts with Flash-Lite prechecks for classification, structure, PII, and risk labels.",
                    "Balanced or grounded primary routes are allowed only after prechecks; premium primary defaults block the plan.",
                    "The service returns route metadata only and never calls NewAPI, Gemini, gateways, or external datasets.",
                ],
            },
            "summary": {
                "case_count": len(case_rows),
                "cheap_precheck_case_count": sum(1 for row in case_rows if row["cheap_precheck_required"]),
                "lowest_primary_case_count": sum(
                    1 for row in case_rows if row["primary_route"]["cost_tier"] == "lowest"
                ),
                "balanced_primary_case_count": sum(1 for row in case_rows if row["primary_route"]["cost_tier"] == "low"),
                "premium_primary_case_count": len(premium_rows),
                "routed_to_recommended_count": len(routed_rows),
                "override_count": sum(1 for row in case_rows if row["override_applied"]),
                "coverage_status": coverage["status"],
                "coverage_document_type_count": coverage["summary"]["covered_document_type_count"],
                "estimated_precheck_cost_usd": round(estimated_precheck_cost, 6),
                "estimated_primary_cost_usd": round(estimated_primary_cost, 6),
                "model_calls": "not_required",
                "network_access": "disabled",
                "raw_fixture_snippets_returned": False,
                "raw_outputs_returned": False,
            },
            "source_summaries": {
                "legal_document_benchmark_suite": {
                    "status": suite["status"],
                    "case_count": suite["summary"]["case_count"],
                    "check_count": suite["summary"]["check_count"],
                    "data_source": suite["summary"]["data_source"],
                },
                "legal_document_benchmark_coverage": {
                    "status": coverage["status"],
                    "covered_document_type_count": coverage["summary"]["covered_document_type_count"],
                    "missing_document_type_count": coverage["summary"]["missing_document_type_count"],
                    "returns_snippets": coverage["privacy_boundary"]["returns_snippets"],
                },
            },
            "route_policy": {
                "precheck_tasks": list(PRECHECK_TASKS),
                "precheck_model": "gemini-2.5-flash-lite",
                "premium_default_allowed": False,
                "balanced_after_precheck_allowed": True,
                "operator_override_policy": "premium primary routes remain blocked for this local benchmark plan",
                "route_budget_basis": "local catalog cost tiers and metadata-only pricing-unit assumptions",
            },
            "case_route_rows": case_rows,
            "checks": checks,
            "blocking_check_ids": blocking_check_ids,
            "warning_check_ids": warning_check_ids,
            "recommended_actions": self._recommended_actions(case_rows, blocking_check_ids, warning_check_ids),
            "privacy_boundary": {
                "returns_fixture_snippets": False,
                "returns_raw_candidate_outputs": False,
                "returns_raw_model_outputs": False,
                "returns_prompts": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_access": False,
                "output_scope": "fixture ids, document types, route tasks, model ids, cost tiers, reason codes, and estimated route costs",
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "production_accuracy_claimed": False,
                "real_client_document_coverage_claimed": False,
                "allowed_claim": (
                    "Local synthetic legal-document benchmark cases have a metadata-only cheap-first Gemini route plan."
                ),
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py -q",
            ],
        }

    def _case_route_row(self, case: dict[str, Any], override: RouteOverride | None) -> dict[str, Any]:
        required_sections = list(case.get("required_sections") or [])
        expected_citations = list(case.get("expected_citations") or [])
        expected_risk_labels = list(case.get("expected_risk_labels") or [])
        document_type = str(case.get("document_type") or "")
        primary_task = override.primary_task if override and override.primary_task else self._primary_task(case)
        explicit_model = override.primary_model if override else None
        allow_over_budget_model = bool(override.allow_over_budget_model) if override else False
        precheck_route = resolve_runtime_model(None, task="classification")
        primary_route = resolve_runtime_model(
            explicit_model,
            task=primary_task,
            allow_over_budget_model=allow_over_budget_model,
        )
        primary_ladder = self.candidate_selector.default_ladder_for_task(primary_task)
        risk_score = self._route_risk_score(
            required_sections=required_sections,
            expected_citations=expected_citations,
            expected_risk_labels=expected_risk_labels,
            primary_task=primary_task,
        )
        return {
            "case_id": case["id"],
            "title": case["title"],
            "document_type": document_type,
            "matter_type": case["matter_type"],
            "route_band": self._route_band(primary_route.cost_tier, risk_score),
            "cheap_precheck_required": True,
            "precheck_route": {
                "task": precheck_route.task,
                "model": precheck_route.resolved_model,
                "cost_tier": precheck_route.cost_tier,
                "reason_codes": precheck_route.reason_codes,
            },
            "primary_task": primary_task,
            "primary_route": {
                "requested_model": primary_route.requested_model,
                "resolved_model": primary_route.resolved_model,
                "canonical_model": primary_route.requested_canonical_model,
                "cost_tier": primary_route.cost_tier,
                "budget_mode": primary_route.budget_mode,
                "max_cost_tier": primary_route.max_cost_tier,
                "requires_operator_review": primary_route.requires_operator_review,
                "routed_to_recommended_model": primary_route.routed_to_recommended_model,
                "recommended_model": primary_route.recommended_model,
                "reason_codes": primary_route.reason_codes,
            },
            "escalation_ladder": [
                {
                    "order": item["order"],
                    "model": item["model"],
                    "cost_tier": item["cost_tier"],
                    "role": item["role"],
                    "default_eligible": item["default_eligible"],
                    "candidate_stage": item["candidate_stage"],
                }
                for item in primary_ladder[:5]
            ],
            "route_risk_score": risk_score,
            "required_section_count": len(required_sections),
            "expected_citation_count": len(expected_citations),
            "expected_risk_label_count": len(expected_risk_labels),
            "estimated_precheck_cost_usd": self._estimated_cost(
                precheck_route.resolved_model,
                PRECHECK_PROMPT_TOKENS,
                PRECHECK_COMPLETION_TOKENS,
            ),
            "estimated_primary_cost_usd": self._estimated_cost(
                primary_route.resolved_model,
                PRIMARY_PROMPT_TOKENS.get(primary_task, PRIMARY_PROMPT_TOKENS["review"]),
                PRIMARY_COMPLETION_TOKENS.get(primary_task, PRIMARY_COMPLETION_TOKENS["review"]),
            ),
            "override_applied": override is not None,
            "raw_fixture_snippet_returned": False,
        }

    def _route_overrides(self, raw: Any) -> dict[str, RouteOverride]:
        if not isinstance(raw, dict):
            return {}
        overrides: dict[str, RouteOverride] = {}
        for case_id, value in raw.items():
            safe_case_id = str(case_id or "").strip()[:120]
            if not safe_case_id or not isinstance(value, dict):
                continue
            primary_task = self._safe_task(value.get("primary_task"))
            primary_model = safe_model_id(value.get("primary_model"))
            overrides[safe_case_id] = RouteOverride(
                primary_task=primary_task or None,
                primary_model=primary_model or None,
                allow_over_budget_model=value.get("allow_over_budget_model") is True,
            )
        return overrides

    def _checks(
        self,
        case_rows: list[dict[str, Any]],
        suite: dict[str, Any],
        coverage: dict[str, Any],
    ) -> list[dict[str, Any]]:
        premium_case_ids = [
            row["case_id"] for row in case_rows if row["primary_route"]["cost_tier"] in PREMIUM_COST_TIERS
        ]
        missing_precheck_case_ids = [row["case_id"] for row in case_rows if not row["cheap_precheck_required"]]
        unpriced_case_ids = [row["case_id"] for row in case_rows if row["primary_route"]["cost_tier"] is None]
        return [
            self._check(
                "benchmark-suite-ready",
                "pass" if suite["status"] == "ready" else "fail",
                "Legal document benchmark suite supplies local synthetic case metadata.",
                source="legal_document_benchmark_suite",
            ),
            self._check(
                "document-coverage-ready",
                "pass" if coverage["summary"]["missing_document_type_count"] == 0 else "warn",
                "Benchmark route plan is joined to the current document-type coverage matrix.",
                source="legal_document_benchmark_coverage",
            ),
            self._check(
                "cheap-precheck-attached",
                "pass" if not missing_precheck_case_ids else "fail",
                "Every benchmark case must start with a Flash-Lite precheck before balanced or grounded routes.",
                case_ids=missing_precheck_case_ids,
            ),
            self._check(
                "no-premium-primary-defaults",
                "pass" if not premium_case_ids else "fail",
                "Premium models cannot be primary defaults for local legal-document benchmark smoke runs.",
                case_ids=premium_case_ids,
            ),
            self._check(
                "priced-primary-routes",
                "pass" if not unpriced_case_ids else "warn",
                "Primary route models should have catalog pricing before they are used in runbooks.",
                case_ids=unpriced_case_ids,
            ),
            self._check(
                "metadata-only-boundary",
                "pass",
                "Route planning returns only model metadata, fixture ids, and counts; it does not echo snippets or outputs.",
            ),
        ]

    def _check(
        self,
        check_id: str,
        status: str,
        description: str,
        *,
        case_ids: list[str] | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        return {
            "id": check_id,
            "status": status,
            "description": description,
            "case_ids": case_ids or [],
            "source": source,
        }

    def _primary_task(self, case: dict[str, Any]) -> str:
        return DOCUMENT_PRIMARY_TASKS.get(str(case.get("document_type") or ""), "review")

    def _safe_task(self, value: Any) -> str:
        raw = str(value or "").strip().lower().replace("_", "-")[:80]
        if raw in {"classification", "fast", "review", "document-generation", "grounded-research", "pdf"}:
            return raw
        return ""

    def _route_risk_score(
        self,
        *,
        required_sections: list[str],
        expected_citations: list[str],
        expected_risk_labels: list[str],
        primary_task: str,
    ) -> int:
        score = len(required_sections) + len(expected_citations) * 2 + len(expected_risk_labels) * 3
        if primary_task in {"grounded-research", "document-generation"}:
            score += 4
        return score

    def _route_band(self, cost_tier: str | None, risk_score: int) -> str:
        if cost_tier in PREMIUM_COST_TIERS:
            return "blocked_premium_default"
        if cost_tier == "lowest" and risk_score <= 20:
            return "cheap_primary_after_precheck"
        if cost_tier == "lowest":
            return "cheap_grounded_or_structured"
        return "balanced_after_cheap_precheck"

    def _estimated_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
        profile = model_profile(model)
        if profile is None:
            return None
        estimate = estimate_token_cost_usd(model, prompt_tokens, completion_tokens)
        return round(estimate, 6) if estimate is not None else None

    def _recommended_actions(
        self,
        case_rows: list[dict[str, Any]],
        blocking_check_ids: list[str],
        warning_check_ids: list[str],
    ) -> list[str]:
        actions: list[str] = []
        if "no-premium-primary-defaults" in blocking_check_ids:
            actions.append("Move premium benchmark primary routes back behind Flash-Lite or Flash review gates.")
        if "priced-primary-routes" in warning_check_ids:
            actions.append("Add catalog pricing before relying on any unpriced benchmark route.")
        if any(row["primary_route"]["cost_tier"] == "low" for row in case_rows):
            actions.append("Run Flash-Lite prechecks first, then send only surviving generation/review cases to Flash.")
        actions.append("Keep local benchmark route runs metadata-only until explicit gateway execution evidence is reviewed.")
        return list(dict.fromkeys(actions))
