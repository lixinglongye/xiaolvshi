import re

import pytest

from services.legal_rag_embedding_batch_approval_packet import LegalRagEmbeddingBatchApprovalPacketService


def test_embedding_batch_approval_packet_builds_metadata_only_packet():
    packet = LegalRagEmbeddingBatchApprovalPacketService().build_packet()

    assert packet["id"] == "legal-rag-embedding-batch-approval-packet"
    assert packet["schema_version"] == "legal-rag-embedding-batch-approval-packet-v1"
    assert packet["status"] == "approval_blocked"
    assert packet["summary"]["approval_item_count"] == 6
    assert packet["summary"]["ready_for_approval_count"] == 2
    assert packet["summary"]["hold_for_review_count"] == 2
    assert packet["summary"]["blocked_approval_count"] == 2
    assert packet["summary"]["required_signoff_count"] == 6
    assert packet["summary"]["approved_count"] == 0
    assert packet["summary"]["planned_batch_total"] == 7
    assert packet["summary"]["estimated_batch_cost_usd"] == 0.000957
    assert packet["summary"]["max_parallel_embedding_requests"] == 1
    assert packet["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert packet["linked_gate_summary"]["legal_rag_embedding_batch_budget_gate"] == "blocked"
    assert packet["approval_policy"]["embedding_run_allowed"] is False
    assert packet["approval_policy"]["model_call_allowed"] is False
    assert packet["approval_policy"]["approval_record_written"] is False


def test_embedding_batch_approval_items_map_ready_hold_and_block_actions():
    packet = LegalRagEmbeddingBatchApprovalPacketService().build_packet()
    ready = [item for item in packet["approval_items"] if item["approval_status"] == "ready_for_maintainer_approval"]
    hold = [item for item in packet["approval_items"] if item["approval_status"] == "hold_for_review"]
    blocked = [item for item in packet["approval_items"] if item["approval_status"] == "blocked_until_budget_ready"]

    assert len(ready) == 2
    assert len(hold) == 2
    assert len(blocked) == 2
    assert all(item["run_action"] == "advance_next_embedding_batch_review_only" for item in ready)
    assert all(item["run_action"] == "hold_embedding_batch_for_review" for item in hold)
    assert all(item["run_action"] == "block_embedding_run" for item in blocked)
    assert all(item["required_signoffs"] == ["maintainer_owner", "rag_index_reviewer"] for item in ready)
    assert all(item["required_signoffs"] == ["rag_index_reviewer"] for item in hold)
    assert all(item["required_signoffs"] == [] for item in blocked)

    for item in packet["approval_items"]:
        assert item["queue_order"] >= 1
        assert item["max_parallel_embedding_requests"] == 1
        assert item["embedding_model"] == "gemini-embedding-001"
        assert "legal-rag-embedding-batch-budget-gate" in item["linked_gate_ids"]
        assert item["approval_record_written"] is False
        assert item["embedding_run_allowed"] is False
        assert item["model_call_allowed"] is False
        assert item["index_write_allowed"] is False
        assert item["privacy_boundary"]["source_chunks_returned"] is False
        assert item["privacy_boundary"]["embedding_vectors_returned"] is False
        assert item["privacy_boundary"]["approver_identity_returned"] is False


def test_embedding_batch_approval_packet_blocks_unsafe_custom_metadata_without_echoing_values():
    secret = "sk-" + ("D" * 24)
    raw_text = "UNSAFE_APPROVAL_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK"
    email = "approval-client@example.invalid"
    packet = LegalRagEmbeddingBatchApprovalPacketService().build_packet(
        [
            {
                "source_type": "template",
                "jurisdiction": "CN-National",
                "freshness_status": "fresh",
                "estimated_token_count": 300,
                "section_count": 2,
                "citation_anchor_count": 1,
                "retrieval_locator_present": True,
                "source_id": "do-not-echo-approval-source-id",
                "raw_text": raw_text,
                "api_key": secret,
                "email": email,
                "embedding_vector": [0.1, 0.2],
            }
        ]
    )
    rendered = str(packet)

    assert packet["status"] == "approval_blocked"
    assert packet["approval_items"][0]["approval_status"] == "blocked_until_budget_ready"
    assert "dry_run_row_blocked" in packet["approval_items"][0]["blocking_reason_codes"]
    assert raw_text not in rendered
    assert secret not in rendered
    assert email not in rendered
    assert "do-not-echo-approval-source-id" not in rendered
    assert re.search(r"sk-[A-Za-z0-9]{20,}", rendered) is None


def test_embedding_batch_approval_claim_and_privacy_boundaries_are_safe():
    packet = LegalRagEmbeddingBatchApprovalPacketService().build_packet()

    assert packet["summary"]["approval_record_written"] is False
    assert packet["summary"]["model_called"] is False
    assert packet["summary"]["gateway_called"] is False
    assert packet["summary"]["network_called"] is False
    assert packet["summary"]["embeddings_created"] is False
    assert packet["summary"]["index_written"] is False
    assert packet["claim_boundary"]["maintainer_approval_claimed"] is False
    assert packet["claim_boundary"]["embedding_batch_executed_claimed"] is False
    assert packet["claim_boundary"]["pricing_accuracy_claimed"] is False
    assert packet["privacy_boundary"]["metadata_only"] is True
    assert packet["privacy_boundary"]["returns_source_ids"] is False
    assert packet["privacy_boundary"]["returns_raw_legal_text"] is False
    assert packet["privacy_boundary"]["returns_source_chunks"] is False
    assert packet["privacy_boundary"]["returns_embedding_vectors"] is False
    assert packet["privacy_boundary"]["returns_approver_identity"] is False
    assert packet["privacy_boundary"]["creates_embeddings"] is False
    assert packet["privacy_boundary"]["writes_index"] is False
    assert packet["privacy_boundary"]["writes_approval_record"] is False
    assert packet["input_contract"]["approval_identity_collected"] is False
    assert packet["input_contract"]["approval_record_written"] is False
    assert "source_id" in packet["input_contract"]["forbidden_fields_ignored"]


def test_embedding_batch_approval_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-batch-approval-packet")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["approval_item_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_source_chunks"] is False
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-batch-approval-packet",
        json={
            "source_rows": [
                {
                    "source_type": "template",
                    "jurisdiction": "CN-National",
                    "freshness_status": "fresh",
                    "estimated_token_count": 300,
                    "section_count": 2,
                    "citation_anchor_count": 1,
                    "retrieval_locator_present": True,
                }
            ]
        },
    )

    assert reviewed.status_code == 200
    data = reviewed.json()["data"]
    assert data["status"] == "approval_ready"
    assert data["approval_items"][0]["approval_status"] == "ready_for_maintainer_approval"
    assert data["approval_items"][0]["run_action"] == "advance_next_embedding_batch_review_only"
