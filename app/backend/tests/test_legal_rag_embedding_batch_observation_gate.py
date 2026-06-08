import re

import pytest

from services.legal_rag_embedding_batch_observation_gate import LegalRagEmbeddingBatchObservationGateService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|client@example.invalid|RAW_EMBEDDING_OBSERVATION_TEXT|do-not-echo-source-id"
)


def _ready_source_rows():
    return [
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


def test_embedding_batch_observation_gate_defaults_to_safe_pending_metadata_only_state():
    gate = LegalRagEmbeddingBatchObservationGateService().build_gate()

    assert gate["id"] == "legal-rag-embedding-batch-observation-gate"
    assert gate["schema_version"] == "legal-rag-embedding-batch-observation-gate-v1"
    assert gate["status"] == "index_commit_blocked"
    assert gate["summary"]["observation_row_count"] == 6
    assert gate["summary"]["ready_for_index_review_count"] == 0
    assert gate["summary"]["review_row_count"] == 4
    assert gate["summary"]["blocked_row_count"] == 2
    assert gate["summary"]["pending_observation_count"] == 2
    assert gate["summary"]["expected_batch_total"] == 7
    assert gate["summary"]["observed_batch_total"] == 0
    assert gate["summary"]["observed_vector_slot_total"] == 0
    assert gate["summary"]["max_parallel_embedding_requests"] == 1
    assert gate["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert gate["linked_gate_summary"]["legal_rag_embedding_batch_approval_packet"] == "approval_blocked"
    assert gate["observation_policy"]["embedding_creation_allowed"] is False
    assert gate["observation_policy"]["model_call_allowed"] is False
    assert gate["observation_policy"]["index_write_allowed"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["writes_index"] is False


def test_embedding_batch_observation_gate_accepts_sanitized_success_observation_for_ready_source_row():
    gate = LegalRagEmbeddingBatchObservationGateService().build_gate(
        source_rows=_ready_source_rows(),
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
                }
            ]
        },
    )
    row = gate["observation_rows"][0]

    assert gate["status"] == "ready_for_index_review"
    assert gate["summary"]["ready_for_index_review_count"] == 1
    assert gate["summary"]["review_row_count"] == 0
    assert gate["summary"]["blocked_row_count"] == 0
    assert gate["summary"]["observed_batch_total"] == 1
    assert gate["summary"]["observed_vector_slot_total"] == 1
    assert row["approval_status"] == "ready_for_maintainer_approval"
    assert row["observation_status"] == "ready_for_index_review"
    assert row["release_action"] == "allow_index_commit_review_only"
    assert row["reason_codes"] == ["embedding_batch_observation_ready"]
    assert row["privacy_boundary"]["embedding_vectors_returned"] is False
    assert "legal-rag-embedding-batch-approval-packet" in row["linked_gate_ids"]


def test_embedding_batch_observation_gate_maps_mismatch_and_failed_observations_to_review_and_blocked():
    source_rows = _ready_source_rows() + [
        {
            "source_type": "statute",
            "jurisdiction": "CN-National",
            "freshness_status": "fresh",
            "estimated_token_count": 400,
            "section_count": 2,
            "citation_anchor_count": 1,
            "retrieval_locator_present": True,
        }
    ]
    gate = LegalRagEmbeddingBatchObservationGateService().build_gate(
        source_rows=source_rows,
        observation_rows={
            "embedding_observations": [
                {
                    "queue_order": 1,
                    "observed_status": "success",
                    "observed_batch_count": 1,
                    "observed_chunk_count": 1,
                    "observed_vector_slot_count": 0,
                    "observed_token_count": 290,
                    "observed_cost_usd": 0.00002,
                },
                {
                    "queue_order": 2,
                    "observed_status": "failed",
                    "observed_batch_count": 1,
                    "observed_chunk_count": 2,
                    "observed_vector_slot_count": 0,
                    "observed_token_count": 390,
                    "observed_cost_usd": 0.00003,
                },
            ]
        },
    )
    rows = gate["observation_rows"]

    assert gate["status"] == "index_commit_blocked"
    assert gate["summary"]["ready_for_index_review_count"] == 0
    assert gate["summary"]["review_row_count"] == 1
    assert gate["summary"]["blocked_row_count"] == 1
    assert rows[0]["observation_status"] == "review_required"
    assert "observed_vector_slot_count_mismatch" in rows[0]["reason_codes"]
    assert rows[0]["release_action"] == "hold_for_observation_review"
    assert rows[1]["observation_status"] == "blocked"
    assert "embedding_batch_observed_failure:failed" in rows[1]["reason_codes"]
    assert rows[1]["release_action"] == "block_index_commit"


def test_embedding_batch_observation_gate_ignores_unsafe_payload_values_without_echoing_them():
    secret = "sk-" + ("E" * 24)
    gate = LegalRagEmbeddingBatchObservationGateService().build_gate(
        source_rows=[
            {
                **_ready_source_rows()[0],
                "source_id": "do-not-echo-source-id",
                "raw_text": "RAW_EMBEDDING_OBSERVATION_TEXT",
                "api_key": secret,
                "email": "client@example.invalid",
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
                    "source_id": "do-not-echo-source-id",
                    "raw_legal_text": "RAW_EMBEDDING_OBSERVATION_TEXT",
                    "api_key": secret,
                    "email": "client@example.invalid",
                    "embedding_vector": [0.1, 0.2],
                    "approver_email": "client@example.invalid",
                }
            ]
        },
    )
    rendered = str(gate)

    assert "source_id" in gate["input_contract"]["forbidden_fields_ignored"]
    assert "source_approval_item_id" in gate["input_contract"]["forbidden_fields_ignored"]
    assert gate["input_contract"]["source_id_echoed"] is False
    assert gate["input_contract"]["approval_identity_collected"] is False
    assert "RAW_EMBEDDING_OBSERVATION_TEXT" not in rendered
    assert "do-not-echo-source-id" not in rendered
    assert "client@example.invalid" not in rendered
    assert secret not in rendered
    assert not SENSITIVE_PATTERN.search(rendered)


def test_embedding_batch_observation_claim_and_privacy_boundaries_are_safe():
    gate = LegalRagEmbeddingBatchObservationGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["embeddings_created_by_gate"] is False
    assert gate["summary"]["index_written"] is False
    assert gate["claim_boundary"]["maintainer_approval_claimed"] is False
    assert gate["claim_boundary"]["embedding_batch_executed_claimed_by_gate"] is False
    assert gate["claim_boundary"]["index_commit_claimed"] is False
    assert gate["claim_boundary"]["pricing_accuracy_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_source_approval_item_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_source_chunks"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["returns_approver_identity"] is False
    assert gate["privacy_boundary"]["creates_embeddings"] is False
    assert gate["privacy_boundary"]["writes_index"] is False
    assert gate["privacy_boundary"]["writes_approval_record"] is False


def test_embedding_batch_observation_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-batch-observation-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["observation_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-batch-observation-gate",
        json={
            "source_rows": _ready_source_rows(),
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
            ],
        },
    )

    assert reviewed.status_code == 200
    data = reviewed.json()["data"]
    assert data["status"] == "ready_for_index_review"
    assert data["observation_rows"][0]["release_action"] == "allow_index_commit_review_only"
