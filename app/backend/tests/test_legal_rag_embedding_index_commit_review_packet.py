import re

import pytest

from services.legal_rag_embedding_index_commit_review_packet import (
    LegalRagEmbeddingIndexCommitReviewPacketService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|commit-client@example.invalid|RAW_INDEX_COMMIT_TEXT|do-not-echo-commit-source-id"
)


def _source_rows(count: int = 1):
    return [
        {
            "source_type": source_type,
            "jurisdiction": "CN-National",
            "freshness_status": "fresh",
            "estimated_token_count": 300 + index * 100,
            "section_count": 2,
            "citation_anchor_count": 1,
            "retrieval_locator_present": True,
        }
        for index, source_type in enumerate(["template", "statute", "case"][:count])
    ]


def _ready_observation_payload():
    return {
        "observations": [
            {
                "queue_order": 1,
                "observed_status": "success",
                "observed_batch_count": 1,
                "observed_chunk_count": 1,
                "observed_vector_slot_count": 1,
                "observed_token_count": 290,
                "observed_cost_usd": 0.00002,
            }
        ]
    }


def test_index_commit_review_packet_defaults_to_blocked_metadata_only_packet():
    packet = LegalRagEmbeddingIndexCommitReviewPacketService().build_packet()

    assert packet["id"] == "legal-rag-embedding-index-commit-review-packet"
    assert packet["schema_version"] == "legal-rag-embedding-index-commit-review-packet-v1"
    assert packet["status"] == "commit_review_blocked"
    assert packet["summary"]["commit_review_item_count"] == 6
    assert packet["summary"]["ready_for_commit_review_count"] == 0
    assert packet["summary"]["hold_for_commit_review_count"] == 4
    assert packet["summary"]["blocked_commit_review_count"] == 2
    assert packet["summary"]["commit_record_written"] is False
    assert packet["summary"]["index_commit_allowed_by_packet"] is False
    assert packet["summary"]["observed_vector_slot_total"] == 0
    assert packet["summary"]["expected_vector_slot_total"] == 30
    assert packet["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert packet["linked_gate_summary"]["legal_rag_embedding_batch_observation_gate"] == "index_commit_blocked"
    assert packet["commit_review_policy"]["index_commit_allowed"] is False
    assert packet["commit_review_policy"]["model_call_allowed"] is False
    assert packet["commit_review_policy"]["database_write_allowed"] is False
    assert packet["privacy_boundary"]["returns_embedding_vectors"] is False
    assert packet["privacy_boundary"]["writes_index"] is False


def test_index_commit_review_packet_maps_ready_observation_to_external_review_only():
    packet = LegalRagEmbeddingIndexCommitReviewPacketService().build_packet(
        source_rows=_source_rows(1),
        observation_rows=_ready_observation_payload(),
    )
    item = packet["commit_review_items"][0]

    assert packet["status"] == "commit_review_ready"
    assert packet["summary"]["ready_for_commit_review_count"] == 1
    assert packet["summary"]["hold_for_commit_review_count"] == 0
    assert packet["summary"]["blocked_commit_review_count"] == 0
    assert item["commit_review_status"] == "ready_for_maintainer_commit_review"
    assert item["commit_review_action"] == "prepare_external_index_commit_review"
    assert item["required_signoffs"] == ["maintainer_owner", "rag_index_reviewer", "privacy_reviewer"]
    assert item["reason_codes"] == ["embedding_index_commit_review_ready"]
    assert item["commit_record_written"] is False
    assert item["index_commit_allowed"] is False
    assert item["privacy_boundary"]["index_written"] is False
    assert "legal-rag-embedding-batch-observation-gate" in item["linked_gate_ids"]


def test_index_commit_review_packet_maps_review_and_blocked_observations_to_hold_and_block():
    packet = LegalRagEmbeddingIndexCommitReviewPacketService().build_packet(
        source_rows=_source_rows(3),
        observation_rows={
            "embedding_observations": [
                {
                    "queue_order": 1,
                    "observed_status": "success",
                    "observed_batch_count": 1,
                    "observed_chunk_count": 1,
                    "observed_vector_slot_count": 1,
                    "observed_token_count": 290,
                    "observed_cost_usd": 0.00002,
                },
                {
                    "queue_order": 2,
                    "observed_status": "success",
                    "observed_batch_count": 1,
                    "observed_chunk_count": 1,
                    "observed_vector_slot_count": 0,
                    "observed_token_count": 390,
                    "observed_cost_usd": 0.00003,
                },
                {
                    "queue_order": 3,
                    "observed_status": "failed",
                    "observed_batch_count": 1,
                    "observed_chunk_count": 1,
                    "observed_vector_slot_count": 0,
                    "observed_token_count": 490,
                    "observed_cost_usd": 0.00004,
                },
            ]
        },
    )
    rows = packet["commit_review_items"]

    assert packet["status"] == "commit_review_blocked"
    assert packet["summary"]["ready_for_commit_review_count"] == 1
    assert packet["summary"]["hold_for_commit_review_count"] == 1
    assert packet["summary"]["blocked_commit_review_count"] == 1
    assert rows[0]["commit_review_status"] == "ready_for_maintainer_commit_review"
    assert rows[1]["commit_review_status"] == "hold_for_commit_review"
    assert rows[1]["commit_review_action"] == "hold_index_commit_for_observation_review"
    assert "observed_vector_slot_count_mismatch" in rows[1]["blocking_reason_codes"]
    assert "observation_row_requires_commit_review" in rows[1]["reason_codes"]
    assert rows[2]["commit_review_status"] == "blocked_until_observation_ready"
    assert rows[2]["commit_review_action"] == "block_index_commit"
    assert "embedding_batch_observed_failure:failed" in rows[2]["blocking_reason_codes"]
    assert "observation_row_blocks_index_commit" in rows[2]["reason_codes"]


def test_index_commit_review_packet_ignores_unsafe_payload_without_echoing_values():
    secret = "sk-" + ("F" * 24)
    packet = LegalRagEmbeddingIndexCommitReviewPacketService().build_packet(
        source_rows=[
            {
                **_source_rows(1)[0],
                "source_id": "do-not-echo-commit-source-id",
                "raw_text": "RAW_INDEX_COMMIT_TEXT",
                "api_key": secret,
                "email": "commit-client@example.invalid",
                "embedding_vector": [0.1, 0.2],
            }
        ],
        observation_rows={
            "observations": [
                {
                    "queue_order": 1,
                    "observed_status": "success",
                    "observed_batch_count": 1,
                    "observed_chunk_count": 1,
                    "observed_vector_slot_count": 1,
                    "observed_token_count": 290,
                    "observed_cost_usd": 0.00002,
                    "source_id": "do-not-echo-commit-source-id",
                    "raw_legal_text": "RAW_INDEX_COMMIT_TEXT",
                    "api_key": secret,
                    "committer_email": "commit-client@example.invalid",
                    "embedding_vector": [0.1, 0.2],
                }
            ]
        },
    )
    rendered = str(packet)

    assert "source_id" in packet["input_contract"]["forbidden_fields_ignored"]
    assert "committer_email" in packet["input_contract"]["forbidden_fields_ignored"]
    assert packet["input_contract"]["source_id_echoed"] is False
    assert packet["input_contract"]["committer_identity_collected"] is False
    assert "RAW_INDEX_COMMIT_TEXT" not in rendered
    assert "do-not-echo-commit-source-id" not in rendered
    assert "commit-client@example.invalid" not in rendered
    assert secret not in rendered
    assert not SENSITIVE_PATTERN.search(rendered)


def test_index_commit_review_packet_claim_and_privacy_boundaries_are_safe():
    packet = LegalRagEmbeddingIndexCommitReviewPacketService().build_packet()

    assert packet["summary"]["model_called"] is False
    assert packet["summary"]["gateway_called"] is False
    assert packet["summary"]["network_called"] is False
    assert packet["summary"]["embeddings_created"] is False
    assert packet["summary"]["index_written"] is False
    assert packet["claim_boundary"]["maintainer_commit_approval_claimed"] is False
    assert packet["claim_boundary"]["index_commit_claimed"] is False
    assert packet["claim_boundary"]["automatic_index_write_claimed"] is False
    assert packet["claim_boundary"]["embedding_batch_executed_claimed_by_packet"] is False
    assert packet["privacy_boundary"]["metadata_only"] is True
    assert packet["privacy_boundary"]["returns_source_ids"] is False
    assert packet["privacy_boundary"]["returns_approval_item_ids"] is False
    assert packet["privacy_boundary"]["returns_raw_legal_text"] is False
    assert packet["privacy_boundary"]["returns_source_chunks"] is False
    assert packet["privacy_boundary"]["returns_embedding_vectors"] is False
    assert packet["privacy_boundary"]["returns_committer_identity"] is False
    assert packet["privacy_boundary"]["creates_embeddings"] is False
    assert packet["privacy_boundary"]["writes_index"] is False
    assert packet["privacy_boundary"]["writes_commit_record"] is False


def test_index_commit_review_packet_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-index-commit-review-packet")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["commit_review_item_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-index-commit-review-packet",
        json={
            "source_rows": _source_rows(1),
            **_ready_observation_payload(),
        },
    )

    assert reviewed.status_code == 200
    data = reviewed.json()["data"]
    assert data["status"] == "commit_review_ready"
    assert data["commit_review_items"][0]["commit_review_action"] == "prepare_external_index_commit_review"
