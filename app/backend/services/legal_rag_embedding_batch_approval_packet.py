from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_rag_embedding_batch_budget_gate import LegalRagEmbeddingBatchBudgetGateService
from services.model_catalog import canonical_model_id, task_default_model


SCHEMA_VERSION = "legal-rag-embedding-batch-approval-packet-v1"
MAX_PARALLEL_EMBEDDING_REQUESTS = 1


class LegalRagEmbeddingBatchApprovalPacketService:
    """Build metadata-only maintainer approval evidence for embedding batches."""

    def __init__(self, batch_budget_service: LegalRagEmbeddingBatchBudgetGateService | None = None) -> None:
        self.batch_budget_service = batch_budget_service or LegalRagEmbeddingBatchBudgetGateService()

    def build_packet(self, source_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        budget_gate = self.batch_budget_service.build_gate(source_rows)
        approval_items = [
            self._approval_item(index, row)
            for index, row in enumerate(budget_gate["batch_budget_rows"], 1)
        ]
        status_counts = Counter(item["approval_status"] for item in approval_items)
        action_counts = Counter(item["run_action"] for item in approval_items)
        ready = [item for item in approval_items if item["approval_status"] == "ready_for_maintainer_approval"]
        hold = [item for item in approval_items if item["approval_status"] == "hold_for_review"]
        blocked = [item for item in approval_items if item["approval_status"] == "blocked_until_budget_ready"]
        status = "approval_blocked" if blocked else ("approval_review_required" if hold else ("approval_ready" if ready else "not_supplied"))

        return {
            "id": "legal-rag-embedding-batch-approval-packet",
            "title": "Legal RAG embedding batch approval packet",
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "summary": {
                "approval_item_count": len(approval_items),
                "ready_for_approval_count": len(ready),
                "hold_for_review_count": len(hold),
                "blocked_approval_count": len(blocked),
                "required_signoff_count": sum(len(item["required_signoffs"]) for item in approval_items),
                "approved_count": 0,
                "planned_batch_total": budget_gate["summary"]["planned_batch_total"],
                "planned_chunk_total": budget_gate["summary"]["planned_chunk_total"],
                "estimated_token_total": budget_gate["summary"]["estimated_token_total"],
                "estimated_batch_cost_usd": budget_gate["summary"]["estimated_batch_cost_usd"],
                "max_parallel_embedding_requests": MAX_PARALLEL_EMBEDDING_REQUESTS,
                "embedding_default_model": task_default_model("embedding"),
                "embedding_default_canonical_model": canonical_model_id(task_default_model("embedding")),
                "batch_budget_gate_status": budget_gate["status"],
                "approval_record_written": False,
                "model_called": False,
                "gateway_called": False,
                "newapi_called": False,
                "network_called": False,
                "embeddings_created": False,
                "index_written": False,
                "database_written": False,
                "source_ids_returned": False,
                "raw_legal_text_included": False,
                "source_chunks_included": False,
                "embedding_vectors_included": False,
                "credentials_included": False,
            },
            "approval_items": approval_items,
            "approval_status_counts": dict(sorted(status_counts.items())),
            "run_action_counts": dict(sorted(action_counts.items())),
            "ready_item_ids": [item["id"] for item in ready],
            "hold_item_ids": [item["id"] for item in hold],
            "blocked_item_ids": [item["id"] for item in blocked],
            "linked_gate_summary": {
                "legal_rag_embedding_batch_budget_gate": budget_gate["status"],
                "legal_rag_embedding_index_dry_run_gate": budget_gate["linked_gate_summary"][
                    "legal_rag_embedding_index_dry_run_gate"
                ],
                "legal_rag_embedding_chunk_policy_gate": budget_gate["linked_gate_summary"][
                    "legal_rag_embedding_chunk_policy_gate"
                ],
                "modelops_gemini_embedding_cheap_first_preflight": budget_gate["linked_gate_summary"][
                    "modelops_gemini_embedding_cheap_first_preflight"
                ],
                "embedding_default_model": task_default_model("embedding"),
            },
            "input_contract": {
                "accepted_source_fields": list(budget_gate["input_contract"]["accepted_source_fields"]),
                "accepted_approval_fields": [
                    "source_type",
                    "queue_order",
                    "batch_status",
                    "approval_status",
                    "planned_batch_count",
                    "estimated_token_count",
                    "estimated_batch_cost_usd",
                    "required_signoffs",
                    "run_action",
                ],
                "forbidden_fields_ignored": list(budget_gate["input_contract"]["forbidden_fields_ignored"]),
                "source_id_echoed": False,
                "approval_identity_collected": False,
                "approval_record_written": False,
                "approval_packet_only": True,
            },
            "approval_policy": {
                "method": "metadata_only_embedding_batch_approval_packet",
                "max_parallel_embedding_requests": MAX_PARALLEL_EMBEDDING_REQUESTS,
                "requires_ready_batch_budget_rows": True,
                "requires_maintainer_signoff_for_ready_rows": True,
                "requires_rag_index_reviewer_for_ready_rows": True,
                "holds_review_required_budget_rows": True,
                "blocks_blocked_budget_rows": True,
                "approval_record_written": False,
                "embedding_run_allowed": False,
                "model_call_allowed": False,
                "index_write_allowed": False,
                "database_write_allowed": False,
                "network_allowed": False,
            },
            "claim_boundary": {
                "maintainer_approval_claimed": False,
                "embedding_batch_executed_claimed": False,
                "legal_advice_claimed": False,
                "retrieval_quality_claimed": False,
                "embedding_quality_claimed": False,
                "index_quality_claimed": False,
                "index_commit_claimed": False,
                "automatic_index_write_claimed": False,
                "pricing_accuracy_claimed": False,
                "allowed_claims": [
                    "The repository exposes a metadata-only approval packet before any cheap Gemini embedding batch run.",
                    "Approval packet rows map budget status to serial run actions and required maintainer roles.",
                ],
                "forbidden_claims": [
                    "Do not claim maintainer approval, live embedding execution, vector storage, or index writes from this packet.",
                    "Do not claim retrieval, embedding, legal-answer, or live pricing quality from approval metadata.",
                ],
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_source_ids": False,
                "returns_raw_query": False,
                "returns_user_question": False,
                "returns_retrieved_context": False,
                "returns_raw_legal_text": False,
                "returns_source_chunks": False,
                "returns_embedding_vectors": False,
                "returns_prompts": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "returns_gateway_payloads": False,
                "returns_approver_identity": False,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "calls_model": False,
                "creates_embeddings": False,
                "writes_index": False,
                "writes_database": False,
                "writes_approval_record": False,
                "downloads_datasets": False,
                "network_called": False,
            },
            "recommended_actions": self._recommended_actions(ready, hold, blocked),
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_embedding_batch_approval_packet.py tests/test_legal_rag_embedding_batch_budget_gate.py -q",
                "python -m pytest tests/test_legal_rag_embedding_batch_approval_packet.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _approval_item(self, index: int, budget_row: dict[str, Any]) -> dict[str, Any]:
        budget_status = str(budget_row.get("batch_status") or "blocked")
        approval_status = self._approval_status(budget_status)
        required_signoffs = self._required_signoffs(approval_status)
        reason_codes = [str(code) for code in budget_row.get("reason_codes", []) if str(code).strip()]
        return {
            "id": f"embedding-batch-approval-{index}-{_safe_token(budget_row.get('source_type'))}",
            "source_batch_budget_row_id": str(budget_row.get("id") or f"batch-budget-row-{index}"),
            "source_type": _safe_token(budget_row.get("source_type")),
            "queue_order": index,
            "batch_status": budget_status,
            "approval_status": approval_status,
            "run_action": self._run_action(approval_status),
            "planned_batch_count": _non_negative_int(budget_row.get("planned_batch_count")),
            "planned_chunk_count": _non_negative_int(budget_row.get("planned_chunk_count")),
            "estimated_token_count": _non_negative_int(budget_row.get("estimated_token_count")),
            "estimated_batch_cost_usd": _safe_float(budget_row.get("estimated_batch_cost_usd")),
            "max_parallel_embedding_requests": MAX_PARALLEL_EMBEDDING_REQUESTS,
            "embedding_model": task_default_model("embedding"),
            "canonical_embedding_model": canonical_model_id(task_default_model("embedding")),
            "required_signoffs": required_signoffs,
            "pre_approval_checks": self._pre_approval_checks(approval_status),
            "blocking_reason_codes": [] if approval_status == "ready_for_maintainer_approval" else reason_codes,
            "approval_record_written": False,
            "embedding_run_allowed": False,
            "model_call_allowed": False,
            "index_write_allowed": False,
            "database_write_allowed": False,
            "operator_action": self._operator_action(approval_status),
            "linked_gate_ids": [
                "legal-rag-embedding-batch-approval-packet",
                "legal-rag-embedding-batch-budget-gate",
                "legal-rag-embedding-index-dry-run-gate",
                "legal-rag-embedding-chunk-policy-gate",
                "modelops-gemini-embedding-cheap-first-preflight",
            ],
            "privacy_boundary": {
                "source_ids_returned": False,
                "raw_legal_text_returned": False,
                "source_chunks_returned": False,
                "embedding_vectors_returned": False,
                "approver_identity_returned": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "approval_record_written": False,
                "database_written": False,
                "index_written": False,
                "credentials_returned": False,
            },
        }

    def _approval_status(self, budget_status: str) -> str:
        if budget_status == "ready":
            return "ready_for_maintainer_approval"
        if budget_status == "review_required":
            return "hold_for_review"
        return "blocked_until_budget_ready"

    def _required_signoffs(self, approval_status: str) -> list[str]:
        if approval_status == "ready_for_maintainer_approval":
            return ["maintainer_owner", "rag_index_reviewer"]
        if approval_status == "hold_for_review":
            return ["rag_index_reviewer"]
        return []

    def _pre_approval_checks(self, approval_status: str) -> list[str]:
        if approval_status == "ready_for_maintainer_approval":
            return [
                "confirm-batch-budget-source-metadata-only",
                "confirm-no-raw-source-chunks-or-vectors",
                "confirm-serial-low-resource-run-window",
                "record-maintainer-approval-outside-this-service",
            ]
        if approval_status == "hold_for_review":
            return [
                "review-or-split-laptop-batch-limits",
                "resolve-dry-run-review-codes",
                "record-rag-index-review-outside-this-service",
            ]
        return [
            "resolve-blocked-batch-budget-row",
            "rerun-batch-budget-gate",
            "do-not-start-embedding-run",
        ]

    def _run_action(self, approval_status: str) -> str:
        if approval_status == "ready_for_maintainer_approval":
            return "advance_next_embedding_batch_review_only"
        if approval_status == "hold_for_review":
            return "hold_embedding_batch_for_review"
        return "block_embedding_run"

    def _operator_action(self, approval_status: str) -> str:
        if approval_status == "ready_for_maintainer_approval":
            return "Collect maintainer and RAG index reviewer signoff outside this service before any live embedding run."
        if approval_status == "hold_for_review":
            return "Hold the batch until review-required budget or dry-run evidence is resolved."
        return "Do not start embedding; fix blocked budget, dry-run, or chunk-policy evidence first."

    def _recommended_actions(
        self,
        ready: list[dict[str, Any]],
        hold: list[dict[str, Any]],
        blocked: list[dict[str, Any]],
    ) -> list[str]:
        actions = [
            "Keep approval packets metadata-only; record real approval, if any, outside this service.",
            "Run embedding batches serially with max_parallel_embedding_requests=1 only after ready rows get external signoff.",
        ]
        if blocked:
            actions.append("Resolve blocked budget rows before requesting maintainer approval.")
        if hold:
            actions.append("Review held rows for laptop limits, dry-run review status, and split requirements.")
        if ready:
            actions.append("Attach ready approval item ids to the external runbook before any live provider call.")
        return actions


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float:
    try:
        return round(max(0.0, float(value)), 8)
    except (TypeError, ValueError):
        return 0.0


def _safe_token(value: Any) -> str:
    text = str(value or "unknown").strip()
    return "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in text)[:80] or "unknown"
