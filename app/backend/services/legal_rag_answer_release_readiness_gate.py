from __future__ import annotations

from collections import Counter
import re
from typing import Any

from services.legal_rag_retrieval_observation_gate import LegalRagRetrievalObservationGateService


MAX_RELEASE_ROWS = 20
SAFE_TOKEN_RE = re.compile(r"[^a-z0-9_.:-]+")


class LegalRagAnswerReleaseReadinessGateService:
    """Convert retrieval observation metadata into answer-release readiness evidence."""

    def __init__(
        self,
        *,
        retrieval_observation_service: LegalRagRetrievalObservationGateService | None = None,
    ) -> None:
        self.retrieval_observation_service = retrieval_observation_service or LegalRagRetrievalObservationGateService()

    def build_gate(self, payload: Any = None) -> dict[str, Any]:
        retrieval_gate = self._retrieval_gate(payload)
        rows = [
            self._row(observation_row, index)
            for index, observation_row in enumerate(self._observation_rows(retrieval_gate), start=1)
        ]
        status_counts = Counter(row["answer_release_status"] for row in rows)
        action_counts = Counter(row["answer_release_action"] for row in rows)
        blocked_rows = [row for row in rows if row["answer_release_status"] == "blocked"]
        review_rows = [row for row in rows if row["answer_release_status"] == "review_required"]
        ready_rows = [row for row in rows if row["answer_release_status"] == "ready"]

        return {
            "id": "legal-rag-answer-release-readiness-gate",
            "title": "Legal RAG answer release readiness gate",
            "schema_version": "legal-rag-answer-release-readiness-gate-v1",
            "status": "blocked"
            if blocked_rows
            else ("review_required" if review_rows else ("ready" if ready_rows else "not_run")),
            "summary": {
                "answer_release_row_count": len(rows),
                "ready_answer_count": len(ready_rows),
                "review_required_count": len(review_rows),
                "blocked_answer_count": len(blocked_rows),
                "internal_draft_allowed_count": sum(1 for row in rows if row["internal_answer_draft_allowed"]),
                "citation_packet_required_count": sum(1 for row in rows if row["citation_packet_required"]),
                "lawyer_review_required_count": sum(1 for row in rows if row["lawyer_review_required"]),
                "premium_exception_candidate_count": sum(1 for row in rows if row["premium_exception_candidate"]),
                "client_delivery_allowed_count": 0,
                "retrieval_ready_count": sum(1 for row in rows if row["retrieval_status"] == "ready"),
                "retrieval_review_count": sum(1 for row in rows if row["retrieval_status"] == "review_required"),
                "retrieval_blocked_count": sum(1 for row in rows if row["retrieval_status"] == "blocked"),
                "cheap_first_continue_count": sum(1 for row in rows if row["cheap_first_decision"] == "continue"),
                "cheap_first_verify_or_escalate_count": sum(
                    1 for row in rows if row["cheap_first_decision"] in {"verify", "escalate"}
                ),
                "source_coverage_gap_count": sum(1 for row in rows if row["source_coverage_status"] != "ready"),
                "top_k_gap_count": sum(1 for row in rows if row["top_k_depth_status"] != "sufficient"),
                "jurisdiction_or_freshness_gap_count": sum(
                    1
                    for row in rows
                    if row["jurisdiction_status"] != "matched" or row["freshness_status"] != "fresh"
                ),
                "retrieval_observation_gate_status": retrieval_gate.get("status", "not_run"),
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "gemini_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "raw_query_included": False,
                "raw_user_question_included": False,
                "raw_retrieved_context_included": False,
                "raw_legal_text_included": False,
                "source_ids_returned": False,
                "prompt_included": False,
                "model_output_included": False,
                "credentials_included": False,
                "legal_advice_claimed": False,
                "automatic_client_delivery_allowed": False,
            },
            "answer_release_rows": rows,
            "answer_release_status_counts": dict(sorted(status_counts.items())),
            "answer_release_action_counts": dict(sorted(action_counts.items())),
            "linked_gate_summary": {
                "legal_rag_retrieval_observation_gate": retrieval_gate.get("status", "not_run"),
                "legal_rag_retrieval_diagnostics_gate": "metadata_link_only",
                "legal_rag_authority_citation_gate": "metadata_link_only",
                "legal_rag_abstention_escalation_gate": "metadata_link_only",
                "model_escalation_policy": "cheap_first_metadata_only",
            },
            "input_contract": {
                "accepted_container_keys": [
                    "retrieval_observation_gate",
                    "legal_rag_retrieval_observation_gate",
                    "observation_rows",
                    "retrieval_observations",
                    "observations",
                    "rows",
                ],
                "accepted_row_fields": [
                    "id",
                    "query_intent",
                    "retrieval_status",
                    "release_action",
                    "source_coverage_status",
                    "top_k_depth_status",
                    "jurisdiction_status",
                    "freshness_status",
                    "cheap_first_action",
                    "reason_codes",
                ],
                "raw_text_fields_ignored": [
                    "query",
                    "question",
                    "raw_query",
                    "retrieved_context",
                    "raw_legal_text",
                    "prompt",
                    "model_output",
                    "gateway_payload",
                ],
                "source_id_echoed": False,
                "raw_query_collected": False,
                "retrieved_context_collected": False,
                "client_delivery_materialized": False,
            },
            "answer_release_policy": {
                "method": "deterministic_metadata_join",
                "requires_ready_retrieval_status": True,
                "requires_allow_retrieval_use_action": True,
                "requires_sufficient_top_k_depth": True,
                "requires_matched_jurisdiction": True,
                "requires_fresh_sources": True,
                "requires_citation_packet_for_all_ready_rows": True,
                "allows_internal_answer_draft": bool(ready_rows),
                "allows_client_delivery": False,
                "allows_legal_advice_claim": False,
                "allows_premium_exception_without_review": False,
                "model_call_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "legal_advice_claimed": False,
                "answer_quality_claimed": False,
                "retrieval_quality_claimed": False,
                "public_benchmark_score_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_client_delivery_claimed": False,
                "allowed_claims": [
                    "The repository maps sanitized retrieval observations to metadata-only answer release readiness.",
                    "Ready rows may prepare an internal citation packet for reviewer inspection.",
                ],
                "forbidden_claims": [
                    "Do not claim legal advice quality or automatic client delivery.",
                    "Do not claim live retrieval, model, gateway, or benchmark quality from this gate.",
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
                "calls_model": False,
                "downloads_datasets": False,
                "network_called": False,
                "writes_answer": False,
                "sends_client_delivery": False,
            },
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows, ready_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_answer_release_readiness_gate.py tests/test_legal_rag_retrieval_observation_gate.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _retrieval_gate(self, payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            for key in ("retrieval_observation_gate", "legal_rag_retrieval_observation_gate"):
                value = payload.get(key)
                if isinstance(value, dict) and isinstance(value.get("observation_rows"), list):
                    return value
            for key in ("observation_rows", "retrieval_observation_rows"):
                value = payload.get(key)
                if isinstance(value, list):
                    return {
                        "id": "legal-rag-retrieval-observation-gate",
                        "status": "direct_observation_rows",
                        "observation_rows": value[:MAX_RELEASE_ROWS],
                    }
        return self.retrieval_observation_service.build_gate(payload)

    def _observation_rows(self, retrieval_gate: dict[str, Any]) -> list[dict[str, Any]]:
        rows = retrieval_gate.get("observation_rows")
        if not isinstance(rows, list):
            return []
        return [row for row in rows[:MAX_RELEASE_ROWS] if isinstance(row, dict)]

    def _row(self, observation: dict[str, Any], index: int) -> dict[str, Any]:
        retrieval_status = self._safe_token(observation.get("retrieval_status"), "not_run")
        release_action = self._safe_token(observation.get("release_action"), "block_answer_release")
        source_coverage_status = self._safe_token(observation.get("source_coverage_status"), "gap")
        top_k_depth_status = self._safe_token(observation.get("top_k_depth_status"), "empty")
        jurisdiction_status = self._safe_token(observation.get("jurisdiction_status"), "unknown")
        freshness_status = self._safe_token(observation.get("freshness_status"), "unknown")
        cheap_first_action = observation.get("cheap_first_action") if isinstance(observation.get("cheap_first_action"), dict) else {}
        cheap_first_decision = self._safe_token(cheap_first_action.get("decision"), "review")
        starts_cheap = bool(cheap_first_action.get("starts_cheap"))
        requires_operator_review = bool(cheap_first_action.get("requires_operator_review"))
        reason_codes = self._safe_list(observation.get("reason_codes"))

        status = self._answer_release_status(
            retrieval_status=retrieval_status,
            release_action=release_action,
            source_coverage_status=source_coverage_status,
            top_k_depth_status=top_k_depth_status,
            jurisdiction_status=jurisdiction_status,
            freshness_status=freshness_status,
        )

        return {
            "id": self._safe_token(observation.get("id"), f"answer-release-{index}"),
            "query_intent": self._safe_token(observation.get("query_intent"), "unspecified"),
            "answer_release_status": status,
            "answer_release_action": self._answer_release_action(status),
            "retrieval_status": retrieval_status,
            "retrieval_release_action": release_action,
            "source_coverage_status": source_coverage_status,
            "top_k_depth_status": top_k_depth_status,
            "jurisdiction_status": jurisdiction_status,
            "freshness_status": freshness_status,
            "cheap_first_decision": cheap_first_decision,
            "cheap_first_starts_cheap": starts_cheap,
            "cheap_first_requires_operator_review": requires_operator_review,
            "internal_answer_draft_allowed": status == "ready",
            "citation_packet_required": status in {"ready", "review_required"},
            "lawyer_review_required": status != "ready" or requires_operator_review,
            "premium_exception_candidate": cheap_first_decision in {"verify", "escalate"} and status != "blocked",
            "client_delivery_allowed": False,
            "reason_codes": self._release_reason_codes(
                base_reason_codes=reason_codes,
                status=status,
                retrieval_status=retrieval_status,
                source_coverage_status=source_coverage_status,
                top_k_depth_status=top_k_depth_status,
                jurisdiction_status=jurisdiction_status,
                freshness_status=freshness_status,
                cheap_first_decision=cheap_first_decision,
            ),
            "linked_gate_ids": [
                "legal-rag-retrieval-observation-gate",
                "legal-rag-retrieval-diagnostics-gate",
                "legal-rag-authority-citation-gate",
                "legal-rag-abstention-escalation-gate",
                "model-escalation-policy",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_query_returned": False,
                "user_question_returned": False,
                "retrieved_context_returned": False,
                "raw_legal_text_returned": False,
                "prompt_returned": False,
                "model_output_returned": False,
                "credentials_returned": False,
                "client_delivery_sent": False,
            },
        }

    def _answer_release_status(
        self,
        *,
        retrieval_status: str,
        release_action: str,
        source_coverage_status: str,
        top_k_depth_status: str,
        jurisdiction_status: str,
        freshness_status: str,
    ) -> str:
        if (
            retrieval_status == "blocked"
            or release_action == "block_answer_release"
            or source_coverage_status == "gap"
            or top_k_depth_status == "empty"
        ):
            return "blocked"
        if (
            retrieval_status != "ready"
            or release_action != "allow_retrieval_use"
            or source_coverage_status != "ready"
            or top_k_depth_status != "sufficient"
            or jurisdiction_status != "matched"
            or freshness_status != "fresh"
        ):
            return "review_required"
        return "ready"

    def _answer_release_action(self, status: str) -> str:
        if status == "ready":
            return "prepare_internal_answer_draft_with_citation_packet"
        if status == "review_required":
            return "require_lawyer_review_before_answer_release"
        return "block_answer_release"

    def _release_reason_codes(
        self,
        *,
        base_reason_codes: list[str],
        status: str,
        retrieval_status: str,
        source_coverage_status: str,
        top_k_depth_status: str,
        jurisdiction_status: str,
        freshness_status: str,
        cheap_first_decision: str,
    ) -> list[str]:
        codes = list(base_reason_codes)
        if status == "ready":
            codes = [code for code in codes if code != "retrieval_observation_ready"]
            codes.append("answer_release_ready")
        if status != "ready":
            codes.append(f"answer_release:{status}")
        if retrieval_status != "ready":
            codes.append(f"retrieval_status:{retrieval_status}")
        if source_coverage_status != "ready":
            codes.append(f"source_coverage:{source_coverage_status}")
        if top_k_depth_status != "sufficient":
            codes.append(f"top_k_depth:{top_k_depth_status}")
        if jurisdiction_status != "matched":
            codes.append(f"jurisdiction:{jurisdiction_status}")
        if freshness_status != "fresh":
            codes.append(f"freshness:{freshness_status}")
        if cheap_first_decision in {"verify", "escalate"}:
            codes.append(f"cheap_first:{cheap_first_decision}")
        return self._unique(codes) or ["answer_release_ready"]

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        ready_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocked_rows:
            return [
                "Block Legal RAG answer release until retrieval observation blockers are resolved.",
                "Repair source coverage, top-k depth, jurisdiction, freshness, and citation metadata before drafting an answer.",
                "Do not escalate to premium models or client delivery while retrieval evidence is blocked.",
            ]
        if review_rows:
            return [
                "Route review-required rows to lawyer review before answer release.",
                "Attach citation packets and cheap-first decision metadata to reviewer notes without raw query or retrieved context.",
            ]
        if ready_rows:
            return [
                "Prepare internal answer drafts with citation packets for ready rows.",
                "Keep automatic client delivery disabled until a lawyer or maintainer approves the answer package.",
            ]
        return ["Submit sanitized retrieval observations before claiming answer release readiness."]

    def _safe_token(self, value: Any, fallback: str) -> str:
        text = str(value or "").strip().lower()[:96]
        if not text:
            return fallback
        safe = SAFE_TOKEN_RE.sub("-", text).strip("-")
        return safe or fallback

    def _safe_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [self._safe_token(item, "") for item in value[:16] if self._safe_token(item, "")]

    def _unique(self, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
