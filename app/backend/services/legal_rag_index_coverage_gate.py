from __future__ import annotations

from collections import Counter
from typing import Any

from services.model_escalation_policy import ModelEscalationPolicyService


class LegalRagIndexCoverageGateService:
    """Build metadata-only coverage evidence for Legal RAG index binding plans."""

    def __init__(self, model_escalation_service: ModelEscalationPolicyService | None = None) -> None:
        self.model_escalation_service = model_escalation_service or ModelEscalationPolicyService()

    def build_gate(self, index_plans: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        plans = index_plans if isinstance(index_plans, list) else self._sample_index_plans()
        rows = [self._row_from_plan(plan) for plan in plans if isinstance(plan, dict)]
        status_counts = Counter(row["index_binding_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        coverage_counts = Counter(row["source_coverage_status"] for row in rows)
        locator_counts = Counter(row["locator_status"] for row in rows)
        blocked_rows = [row for row in rows if row["release_action"] == "block_retrieval_plan"]
        review_rows = [row for row in rows if row["release_action"] == "review_index_plan"]

        return {
            "id": "legal-rag-index-coverage-gate",
            "title": "Legal RAG index coverage gate",
            "status": "ready_with_blockers" if blocked_rows else ("ready_with_review" if review_rows else "ready"),
            "summary": {
                "index_plan_row_count": len(rows),
                "ready_plan_count": status_counts.get("ready", 0),
                "review_plan_count": len(review_rows),
                "blocked_plan_count": len(blocked_rows),
                "candidate_source_total": sum(row["candidate_source_count"] for row in rows),
                "selected_source_total": sum(row["selected_source_count"] for row in rows),
                "missing_requested_source_total": sum(row["missing_requested_source_count"] for row in rows),
                "stale_source_total": sum(row["stale_source_count"] for row in rows),
                "missing_locator_total": sum(row["missing_locator_count"] for row in rows),
                "forbidden_filter_total": sum(row["forbidden_filter_count"] for row in rows),
                "jurisdiction_gap_count": sum(1 for row in rows if row["jurisdiction_status"] != "matched"),
                "freshness_gap_count": sum(1 for row in rows if row["freshness_status"] != "fresh"),
                "cheap_first_continue_count": sum(
                    1 for row in rows if row["cheap_first_action"]["decision"] == "continue"
                ),
                "cheap_first_verify_or_escalate_count": sum(
                    1 for row in rows if row["cheap_first_action"]["decision"] in {"verify", "escalate", "stop"}
                ),
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "source_ids_returned": False,
                "raw_query_included": False,
                "raw_retrieved_context_included": False,
                "raw_legal_text_included": False,
                "prompt_included": False,
                "model_output_included": False,
                "credentials_included": False,
            },
            "index_plan_rows": rows,
            "index_binding_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "source_coverage_counts": dict(sorted(coverage_counts.items())),
            "locator_status_counts": dict(sorted(locator_counts.items())),
            "index_plan_policy": {
                "method": "metadata_only_index_binding_coverage_rows",
                "minimum_selected_source_count": 1,
                "requires_locator_for_selected_sources": True,
                "requires_jurisdiction_filter": True,
                "review_due_sources_require_reviewer_review": True,
                "blocks_on_forbidden_query_filters": True,
                "blocks_on_empty_index_coverage": True,
                "blocks_on_missing_retrieval_locator": True,
                "premium_exception_default_allowed": False,
                "cheap_first_default": True,
            },
            "linked_gate_summary": {
                "legal_rag_index_binding": "metadata-only retrieval-plan contract",
                "legal_rag_retrieval_diagnostics_gate": "retrieval quality diagnostics",
                "legal_rag_retrieval_observation_gate": "observed retrieval metadata review",
                "legal_rag_authority_citation_gate": "authority and citation metadata review",
            },
            "input_contract": {
                "accepted_plan_fields": [
                    "id",
                    "query_intent",
                    "filter_validation_status",
                    "candidate_source_count",
                    "selected_source_count",
                    "requested_source_count",
                    "missing_requested_source_count",
                    "stale_source_count",
                    "missing_locator_count",
                    "jurisdiction_status",
                    "freshness_status",
                    "signals",
                ],
                "raw_text_fields_ignored": [
                    "query",
                    "question",
                    "raw_query",
                    "retrieved_context",
                    "raw_legal_text",
                    "prompt",
                    "model_output",
                    "gateway_response",
                    "headers",
                    "authorization",
                    "api_key",
                    "email",
                ],
            },
            "claim_boundary": {
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "index_quality_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_client_delivery_claimed": False,
                "allowed_claims": [
                    "The repository exposes metadata-only index coverage rows for local Legal RAG review.",
                    "The gate links index binding filters, selected source counts, freshness, locator coverage, and cheap-first review boundaries.",
                ],
                "forbidden_claims": [
                    "Do not claim live retrieval accuracy or legal answer accuracy from this metadata-only gate.",
                    "Do not claim public benchmark scores, NewAPI/Gemini execution, or automatic client delivery.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_source_ids": False,
                "returns_raw_query": False,
                "returns_user_question": False,
                "returns_retrieved_context": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "returns_gateway_payloads": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_index_coverage_gate.py tests/test_legal_rag_index_binding.py -q",
                "python -m pytest tests/test_legal_rag_index_coverage_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _sample_index_plans(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "index-contract-primary-fresh",
                "query_intent": "contract_primary_authority",
                "filter_validation_status": "pass",
                "candidate_source_count": 4,
                "selected_source_count": 3,
                "requested_source_count": 2,
                "missing_requested_source_count": 0,
                "stale_source_count": 0,
                "missing_locator_count": 0,
                "jurisdiction_status": "matched",
                "freshness_status": "fresh",
                "signals": [],
            },
            {
                "id": "index-local-rule-review-due",
                "query_intent": "local_rule_review_due",
                "filter_validation_status": "pass",
                "candidate_source_count": 3,
                "selected_source_count": 2,
                "requested_source_count": 2,
                "missing_requested_source_count": 0,
                "stale_source_count": 0,
                "missing_locator_count": 0,
                "jurisdiction_status": "matched",
                "freshness_status": "review_due",
                "signals": ["review_due_source"],
            },
            {
                "id": "index-cross-jurisdiction-drift",
                "query_intent": "same_topic_cross_jurisdiction",
                "filter_validation_status": "warn",
                "candidate_source_count": 3,
                "selected_source_count": 2,
                "requested_source_count": 2,
                "missing_requested_source_count": 0,
                "stale_source_count": 0,
                "missing_locator_count": 0,
                "jurisdiction_status": "mismatch",
                "freshness_status": "fresh",
                "signals": ["needs_context"],
            },
            {
                "id": "index-stale-source-excluded",
                "query_intent": "stale_regulation_review",
                "filter_validation_status": "pass",
                "candidate_source_count": 3,
                "selected_source_count": 1,
                "requested_source_count": 2,
                "missing_requested_source_count": 0,
                "stale_source_count": 2,
                "missing_locator_count": 0,
                "jurisdiction_status": "matched",
                "freshness_status": "stale_or_review_due",
                "signals": ["weak_citations"],
            },
            {
                "id": "index-missing-locator",
                "query_intent": "template_locator_gap",
                "filter_validation_status": "pass",
                "candidate_source_count": 2,
                "selected_source_count": 2,
                "requested_source_count": 1,
                "missing_requested_source_count": 0,
                "stale_source_count": 0,
                "missing_locator_count": 1,
                "jurisdiction_status": "matched",
                "freshness_status": "fresh",
                "signals": ["quality_gate_fail"],
            },
            {
                "id": "index-forbidden-filter",
                "query_intent": "raw_query_filter_rejected",
                "filter_validation_status": "blocked",
                "candidate_source_count": 0,
                "selected_source_count": 0,
                "requested_source_count": 1,
                "missing_requested_source_count": 1,
                "stale_source_count": 0,
                "missing_locator_count": 0,
                "jurisdiction_status": "unknown",
                "freshness_status": "unknown",
                "forbidden_filter_count": 1,
                "signals": ["privacy_high"],
            },
        ]

    def _row_from_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        candidate_count = _non_negative_int(plan.get("candidate_source_count"))
        selected_count = _non_negative_int(plan.get("selected_source_count"))
        requested_count = _non_negative_int(plan.get("requested_source_count"))
        missing_requested_count = _non_negative_int(plan.get("missing_requested_source_count"))
        stale_count = _non_negative_int(plan.get("stale_source_count"))
        missing_locator_count = _non_negative_int(plan.get("missing_locator_count"))
        forbidden_filter_count = _non_negative_int(plan.get("forbidden_filter_count"))
        filter_status = _token(plan.get("filter_validation_status"), "pass")
        jurisdiction_status = _token(plan.get("jurisdiction_status"), "unknown")
        freshness_status = _token(plan.get("freshness_status"), "unknown")
        source_coverage_status = self._source_coverage_status(
            selected_count=selected_count,
            requested_count=requested_count,
            missing_requested_count=missing_requested_count,
        )
        locator_status = "gap" if missing_locator_count else "ready"
        index_binding_status = self._index_binding_status(
            filter_status=filter_status,
            source_coverage_status=source_coverage_status,
            locator_status=locator_status,
            jurisdiction_status=jurisdiction_status,
            freshness_status=freshness_status,
            forbidden_filter_count=forbidden_filter_count,
        )
        release_action = self._release_action(index_binding_status)
        reason_codes = self._reason_codes(
            filter_status=filter_status,
            source_coverage_status=source_coverage_status,
            locator_status=locator_status,
            jurisdiction_status=jurisdiction_status,
            freshness_status=freshness_status,
            missing_requested_count=missing_requested_count,
            stale_count=stale_count,
            forbidden_filter_count=forbidden_filter_count,
        )
        signals = _list_text(plan.get("signals"))
        if release_action == "block_retrieval_plan" and "quality_gate_fail" not in signals:
            signals.append("quality_gate_fail")
        cheap_first_action = self._cheap_first_action(index_binding_status, signals)

        return {
            "id": _token(plan.get("id"), "index-plan"),
            "query_intent": _token(plan.get("query_intent"), "unknown"),
            "index_binding_status": index_binding_status,
            "release_action": release_action,
            "filter_validation_status": filter_status,
            "source_coverage_status": source_coverage_status,
            "locator_status": locator_status,
            "jurisdiction_status": jurisdiction_status,
            "freshness_status": freshness_status,
            "candidate_source_count": candidate_count,
            "selected_source_count": selected_count,
            "requested_source_count": requested_count,
            "missing_requested_source_count": missing_requested_count,
            "stale_source_count": stale_count,
            "missing_locator_count": missing_locator_count,
            "forbidden_filter_count": forbidden_filter_count,
            "cheap_first_action": cheap_first_action,
            "reason_codes": reason_codes,
            "linked_gate_ids": [
                "legal-rag-index-binding",
                "legal-rag-retrieval-diagnostics-gate",
                "legal-rag-retrieval-observation-gate",
                "legal-rag-authority-citation-gate",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_query_returned": False,
                "retrieved_context_returned": False,
                "raw_legal_text_returned": False,
                "prompt_returned": False,
                "model_output_returned": False,
                "credentials_returned": False,
            },
        }

    def _source_coverage_status(
        self,
        *,
        selected_count: int,
        requested_count: int,
        missing_requested_count: int,
    ) -> str:
        if selected_count <= 0:
            return "gap"
        if missing_requested_count > 0:
            return "partial"
        if requested_count > 0 and selected_count < requested_count:
            return "partial"
        return "ready"

    def _index_binding_status(
        self,
        *,
        filter_status: str,
        source_coverage_status: str,
        locator_status: str,
        jurisdiction_status: str,
        freshness_status: str,
        forbidden_filter_count: int,
    ) -> str:
        if filter_status in {"blocked", "fail", "failed", "invalid", "error", "rejected"} or forbidden_filter_count > 0:
            return "blocked"
        if source_coverage_status == "gap" or locator_status == "gap":
            return "blocked"
        if jurisdiction_status != "matched" or freshness_status != "fresh" or source_coverage_status != "ready":
            return "review_required"
        return "ready"

    def _release_action(self, index_binding_status: str) -> str:
        if index_binding_status == "ready":
            return "allow_retrieval_plan"
        if index_binding_status == "review_required":
            return "review_index_plan"
        return "block_retrieval_plan"

    def _reason_codes(
        self,
        *,
        filter_status: str,
        source_coverage_status: str,
        locator_status: str,
        jurisdiction_status: str,
        freshness_status: str,
        missing_requested_count: int,
        stale_count: int,
        forbidden_filter_count: int,
    ) -> list[str]:
        codes: list[str] = []
        if filter_status != "pass":
            codes.append(f"filter_validation:{filter_status}")
        if forbidden_filter_count:
            codes.append("forbidden_query_filter_present")
        if source_coverage_status != "ready":
            codes.append(f"source_coverage:{source_coverage_status}")
        if missing_requested_count:
            codes.append("requested_sources_not_indexed")
        if locator_status != "ready":
            codes.append("retrieval_locator_missing")
        if jurisdiction_status != "matched":
            codes.append("jurisdiction_mismatch")
        if freshness_status != "fresh":
            codes.append(f"freshness:{freshness_status}")
        if stale_count:
            codes.append("stale_sources_excluded")
        return codes or ["index_binding_ready"]

    def _cheap_first_action(self, index_binding_status: str, signals: list[str]) -> dict[str, Any]:
        task = "fast" if index_binding_status != "blocked" else "review"
        decision = self.model_escalation_service.evaluate(task, signals)
        next_step = decision.get("next_step") or {}
        decision_name = str(decision.get("decision") or "continue")
        recommended_model_alias = next_step.get("model_alias")
        if not recommended_model_alias:
            recommended_model_alias = "manual_review_only" if decision_name == "stop" else "auto-fast"
        return {
            "task": task,
            "decision": decision_name,
            "starts_cheap": bool(next_step.get("mode") == "start" or index_binding_status == "ready"),
            "recommended_model_alias": recommended_model_alias,
            "requires_operator_review": bool(next_step.get("requires_operator_review") or index_binding_status != "ready"),
            "signals": signals,
            "model_called": False,
            "gateway_called": False,
        }

    def _recommended_actions(self, blocked_rows: list[dict[str, Any]], review_rows: list[dict[str, Any]]) -> list[str]:
        actions: list[str] = []
        if blocked_rows:
            actions.append("Block answer generation until forbidden filters, missing source coverage, and missing retrieval locators are fixed.")
        if review_rows:
            actions.append("Review jurisdiction, freshness, and partial source coverage before allowing Legal RAG answers.")
        actions.append("Keep source ids as input-only metadata for the index binding layer and avoid rendering raw legal text or retrieved context.")
        actions.append("Use cheap-first routing only after the metadata-only index plan is ready or explicitly reviewed.")
        return actions


def _token(value: Any, default: str) -> str:
    text = str(value or "").strip().lower().replace(" ", "_")
    return text or default


def _list_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    return [str(item).strip().lower().replace(" ", "_") for item in values if str(item).strip()]


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
