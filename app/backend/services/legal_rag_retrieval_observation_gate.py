from __future__ import annotations

from collections import Counter
import re
from typing import Any

from services.legal_rag_selected_source_validation import LegalRagSelectedSourceValidationService
from services.model_escalation_policy import ModelEscalationPolicyService


MAX_OBSERVATION_ROWS = 20
SAFE_TOKEN_RE = re.compile(r"[^a-z0-9_.:-]+")


class LegalRagRetrievalObservationGateService:
    """Evaluate sanitized Legal RAG retrieval observations without raw text."""

    def __init__(
        self,
        *,
        selected_source_validation_service: LegalRagSelectedSourceValidationService | None = None,
        model_escalation_service: ModelEscalationPolicyService | None = None,
    ) -> None:
        self.selected_source_validation_service = (
            selected_source_validation_service or LegalRagSelectedSourceValidationService()
        )
        self.model_escalation_service = model_escalation_service or ModelEscalationPolicyService()

    def build_gate(self, payload: Any = None) -> dict[str, Any]:
        rows = [self._row(observation, index) for index, observation in enumerate(self._observations(payload), start=1)]
        status_counts = Counter(row["retrieval_status"] for row in rows)
        release_counts = Counter(row["release_action"] for row in rows)
        blocked_rows = [row for row in rows if row["retrieval_status"] == "blocked"]
        review_rows = [row for row in rows if row["retrieval_status"] == "review_required"]
        ready_rows = [row for row in rows if row["retrieval_status"] == "ready"]

        return {
            "id": "legal-rag-retrieval-observation-gate",
            "title": "Legal RAG retrieval observation gate",
            "status": "blocked" if blocked_rows else ("review_required" if review_rows else ("ready" if rows else "not_run")),
            "summary": {
                "observation_row_count": len(rows),
                "ready_row_count": len(ready_rows),
                "review_row_count": len(review_rows),
                "blocked_row_count": len(blocked_rows),
                "selected_source_total": sum(row["selected_source_count"] for row in rows),
                "cited_source_total": sum(row["cited_source_count"] for row in rows),
                "unexpected_cited_source_total": sum(row["source_validation_counts"]["unexpected_source_count"] for row in rows),
                "missing_selected_source_total": sum(
                    row["source_validation_counts"]["missing_selected_source_count"] for row in rows
                ),
                "stale_or_unknown_cited_source_total": sum(
                    row["source_validation_counts"]["stale_source_count"]
                    + row["source_validation_counts"]["unknown_source_count"]
                    for row in rows
                ),
                "top_k_gap_count": sum(1 for row in rows if row["top_k_depth_status"] != "sufficient"),
                "jurisdiction_gap_count": sum(1 for row in rows if row["jurisdiction_status"] != "matched"),
                "freshness_gap_count": sum(1 for row in rows if row["freshness_status"] != "fresh"),
                "cheap_first_continue_count": sum(1 for row in rows if row["cheap_first_action"]["decision"] == "continue"),
                "cheap_first_verify_or_escalate_count": sum(
                    1 for row in rows if row["cheap_first_action"]["decision"] in {"verify", "escalate"}
                ),
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "dataset_downloaded": False,
                "raw_query_included": False,
                "raw_retrieved_context_included": False,
                "raw_legal_text_included": False,
                "prompt_included": False,
                "model_output_included": False,
                "credentials_included": False,
            },
            "observation_rows": rows,
            "retrieval_status_counts": dict(sorted(status_counts.items())),
            "release_action_counts": dict(sorted(release_counts.items())),
            "input_contract": {
                "accepted_container_keys": ["observations", "retrieval_observations", "rows"],
                "accepted_row_fields": [
                    "id",
                    "query_intent",
                    "expected_source_count",
                    "selected_source_ids",
                    "citation_source_ids",
                    "top_k_depth",
                    "jurisdiction_match",
                    "freshness_status",
                    "stale_source_ids",
                    "unknown_source_ids",
                    "signals",
                ],
                "raw_text_fields_ignored": ["query", "question", "retrieved_context", "raw_legal_text", "prompt", "model_output"],
            },
            "claim_boundary": {
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "public_benchmark_score_claimed": False,
                "live_gateway_quality_claimed": False,
                "automatic_client_delivery_claimed": False,
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_raw_query": False,
                "returns_user_question": False,
                "returns_retrieved_context": False,
                "returns_raw_legal_text": False,
                "returns_source_ids": False,
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
            "recommended_actions": self._recommended_actions(blocked_rows, review_rows, ready_rows),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_retrieval_observation_gate.py tests/test_legal_rag_selected_source_validation.py -q",
                "python -m pytest tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _row(self, value: Any, index: int) -> dict[str, Any]:
        observation = value if isinstance(value, dict) else {}
        selected_source_ids = self._list_value(observation, "selected_source_ids", "legal_rag_selected_source_ids")
        citation_source_ids = self._list_value(observation, "citation_source_ids", "cited_source_ids", "source_ids")
        stale_source_ids = self._list_value(observation, "stale_source_ids", "blocked_source_ids")
        unknown_source_ids = self._list_value(observation, "unknown_source_ids")
        expected_source_count = self._positive_int(observation.get("expected_source_count"), len(selected_source_ids) or 1)
        top_k_depth = self._positive_int(observation.get("top_k_depth"), len(selected_source_ids))
        source_validation = self.selected_source_validation_service.validate(
            request_metadata={
                "legal_rag_selected_source_ids": selected_source_ids,
                "stale_source_ids": stale_source_ids,
                "unknown_source_ids": unknown_source_ids,
            },
            citation_map={"citation_source_ids": citation_source_ids},
        )
        source_validation_counts = dict(source_validation["counts"])
        source_coverage_score = round(min(len(selected_source_ids), expected_source_count) / max(1, expected_source_count), 3)
        source_coverage_status = self._source_coverage_status(source_coverage_score)
        top_k_depth_status = self._top_k_depth_status(top_k_depth, expected_source_count)
        jurisdiction_status = self._jurisdiction_status(observation)
        freshness_status = self._freshness_status(observation, source_validation_counts)
        citation_gap = self._bool_value(observation.get("citation_gap")) or source_validation["status"] == "blocked"
        retrieval_gap = self._bool_value(observation.get("retrieval_gap")) or source_coverage_status == "gap"
        retrieval_status = self._retrieval_status(
            source_validation_status=source_validation["status"],
            source_coverage_status=source_coverage_status,
            top_k_depth_status=top_k_depth_status,
            jurisdiction_status=jurisdiction_status,
            freshness_status=freshness_status,
            citation_gap=citation_gap,
            retrieval_gap=retrieval_gap,
        )
        reason_codes = self._reason_codes(
            source_validation_reason_codes=source_validation["reason_codes"],
            source_coverage_status=source_coverage_status,
            top_k_depth_status=top_k_depth_status,
            jurisdiction_status=jurisdiction_status,
            freshness_status=freshness_status,
            citation_gap=citation_gap,
            retrieval_gap=retrieval_gap,
        )
        cheap_first_action = self._cheap_first_action(retrieval_status, self._signals(observation, reason_codes))

        return {
            "id": self._safe_token(observation.get("id"), f"retrieval-observation-{index}"),
            "query_intent": self._safe_token(observation.get("query_intent"), "unspecified"),
            "retrieval_status": retrieval_status,
            "release_action": self._release_action(retrieval_status),
            "source_validation_status": source_validation["status"],
            "source_validation_reason_codes": source_validation["reason_codes"],
            "source_validation_counts": source_validation_counts,
            "source_coverage_status": source_coverage_status,
            "source_coverage_score": source_coverage_score,
            "expected_source_count": expected_source_count,
            "selected_source_count": len(selected_source_ids),
            "cited_source_count": len(citation_source_ids),
            "top_k_depth": top_k_depth,
            "top_k_depth_status": top_k_depth_status,
            "jurisdiction_status": jurisdiction_status,
            "freshness_status": freshness_status,
            "citation_gap": citation_gap,
            "retrieval_gap": retrieval_gap,
            "cheap_first_action": cheap_first_action,
            "reason_codes": reason_codes,
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

    def _observations(self, payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload[:MAX_OBSERVATION_ROWS]
        if not isinstance(payload, dict):
            return []
        for key in ("retrieval_observations", "observations", "rows"):
            value = payload.get(key)
            if isinstance(value, list):
                return value[:MAX_OBSERVATION_ROWS]
        return []

    def _list_value(self, row: dict[str, Any], *keys: str) -> list[Any]:
        for key in keys:
            value = row.get(key)
            if isinstance(value, list):
                return value[:64]
            if isinstance(value, str):
                return [value]
        return []

    def _positive_int(self, value: Any, default: int) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = int(default)
        return max(0, number)

    def _source_coverage_status(self, score: float) -> str:
        if score >= 1.0:
            return "ready"
        if score >= 0.5:
            return "partial"
        return "gap"

    def _top_k_depth_status(self, top_k_depth: int, expected_source_count: int) -> str:
        if top_k_depth >= max(3, expected_source_count):
            return "sufficient"
        if top_k_depth > 0:
            return "shallow"
        return "empty"

    def _jurisdiction_status(self, row: dict[str, Any]) -> str:
        if row.get("jurisdiction_status") in {"matched", "mismatch", "unknown"}:
            return str(row["jurisdiction_status"])
        if "jurisdiction_match" in row:
            return "matched" if self._bool_value(row.get("jurisdiction_match")) else "mismatch"
        return "unknown"

    def _freshness_status(self, row: dict[str, Any], source_validation_counts: dict[str, Any]) -> str:
        value = str(row.get("freshness_status") or "").strip().lower()
        if value in {"fresh", "review_due", "stale", "unknown"}:
            return value
        if source_validation_counts.get("stale_source_count"):
            return "stale"
        if source_validation_counts.get("unknown_source_count"):
            return "unknown"
        return "unknown"

    def _retrieval_status(
        self,
        *,
        source_validation_status: str,
        source_coverage_status: str,
        top_k_depth_status: str,
        jurisdiction_status: str,
        freshness_status: str,
        citation_gap: bool,
        retrieval_gap: bool,
    ) -> str:
        if (
            source_validation_status == "blocked"
            or source_coverage_status == "gap"
            or top_k_depth_status == "empty"
            or (citation_gap and retrieval_gap)
        ):
            return "blocked"
        if (
            source_validation_status == "pass_with_warnings"
            or source_coverage_status == "partial"
            or top_k_depth_status == "shallow"
            or jurisdiction_status != "matched"
            or freshness_status != "fresh"
            or citation_gap
            or retrieval_gap
        ):
            return "review_required"
        return "ready"

    def _release_action(self, status: str) -> str:
        if status == "ready":
            return "allow_retrieval_use"
        if status == "review_required":
            return "review_before_answer"
        return "block_answer_release"

    def _reason_codes(
        self,
        *,
        source_validation_reason_codes: list[str],
        source_coverage_status: str,
        top_k_depth_status: str,
        jurisdiction_status: str,
        freshness_status: str,
        citation_gap: bool,
        retrieval_gap: bool,
    ) -> list[str]:
        codes = list(source_validation_reason_codes)
        if source_coverage_status != "ready":
            codes.append(f"source_coverage:{source_coverage_status}")
        if top_k_depth_status != "sufficient":
            codes.append(f"top_k_depth:{top_k_depth_status}")
        if jurisdiction_status != "matched":
            codes.append(f"jurisdiction:{jurisdiction_status}")
        if freshness_status != "fresh":
            codes.append(f"freshness:{freshness_status}")
        if citation_gap:
            codes.append("citation_gap")
        if retrieval_gap:
            codes.append("retrieval_gap")
        return self._unique(codes) or ["retrieval_observation_ready"]

    def _signals(self, row: dict[str, Any], reason_codes: list[str]) -> list[str]:
        signals = [str(signal).strip().lower() for signal in self._list_value(row, "signals") if str(signal).strip()]
        if any(code.startswith("source_coverage") or code.startswith("top_k_depth") for code in reason_codes):
            signals.append("needs_context")
        if "citation_gap" in reason_codes or any("citation" in code for code in reason_codes):
            signals.append("citation_audit_fail")
        if any(code.startswith("jurisdiction") or code.startswith("freshness") for code in reason_codes):
            signals.append("quality_gate_fail")
        return self._unique(signals)

    def _cheap_first_action(self, retrieval_status: str, signals: list[str]) -> dict[str, Any]:
        task = "fast" if retrieval_status == "ready" else "review"
        decision = self.model_escalation_service.evaluate(task, signals)
        next_step = decision.get("next_step") or {}
        return {
            "task": task,
            "decision": decision["decision"],
            "starts_cheap": retrieval_status == "ready",
            "recommended_model_alias": next_step.get("model_alias", "operator-review"),
            "requires_operator_review": bool(next_step.get("requires_operator_review")) or retrieval_status == "blocked",
            "signals": signals,
            "model_called": False,
            "gateway_called": False,
        }

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        ready_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocked_rows:
            return [
                "Block Legal RAG answer release until selected-source coverage, citation validation, and retrieval depth pass.",
                "Repair source selection metadata before escalating to a premium model; premium exceptions cannot fix missing retrieval context.",
                "Rerun the observation gate with sanitized source ids only; do not paste raw query text or retrieved legal text.",
            ]
        if review_rows:
            return [
                "Route partial coverage, shallow top-k, jurisdiction mismatch, freshness review, or citation gaps to maintainer review.",
                "Keep cheap-first routing for ready rows and use verify/escalate only on deterministic retrieval quality signals.",
            ]
        if ready_rows:
            return ["Observed retrieval metadata is ready for cheap-first Legal RAG use; rerun after index or source changes."]
        return ["Submit sanitized retrieval observations before claiming Legal RAG retrieval readiness."]

    def _safe_token(self, value: Any, fallback: str) -> str:
        text = str(value or "").strip().lower()[:96]
        if not text:
            return fallback
        safe = SAFE_TOKEN_RE.sub("-", text).strip("-")
        return safe or fallback

    def _bool_value(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value or "").strip().lower() in {"1", "true", "yes", "y"}

    def _unique(self, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            safe = str(value or "").strip()
            if safe and safe not in seen:
                seen.add(safe)
                result.append(safe)
        return result
