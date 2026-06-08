import re

import pytest

from services.legal_rag_embedding_index_post_commit_verification_gate import (
    LegalRagEmbeddingIndexPostCommitVerificationGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|commit-client@example.invalid|RAW_POST_COMMIT_TEXT|do-not-echo-post-commit-source-id"
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


def _ready_observations(count: int = 1):
    return {
        "observations": [
            {
                "queue_order": index + 1,
                "observed_status": "success",
                "observed_batch_count": 1,
                "observed_chunk_count": 1,
                "observed_vector_slot_count": 1,
                "observed_token_count": 290 + index * 100,
                "observed_cost_usd": 0.00002 + index * 0.00001,
            }
            for index in range(count)
        ]
    }


def _post_commit_success(count: int = 1):
    return {
        "post_commit_observations": [
            {
                "queue_order": index + 1,
                "post_commit_status": "success",
                "observed_vector_slot_count": 1,
                "observed_index_entry_count": 1,
                "metadata_record_count": 1,
                "retrieval_locator_count": 1,
                "checksum_record_count": 1,
                "failed_entry_count": 0,
                "rollback_required": False,
            }
            for index in range(count)
        ]
    }


def test_post_commit_verification_gate_defaults_to_blocked_metadata_only_gate():
    gate = LegalRagEmbeddingIndexPostCommitVerificationGateService().build_gate()

    assert gate["id"] == "legal-rag-embedding-index-post-commit-verification-gate"
    assert gate["schema_version"] == "legal-rag-embedding-index-post-commit-verification-gate-v1"
    assert gate["status"] == "post_commit_verification_blocked"
    assert gate["summary"]["verification_row_count"] == 6
    assert gate["summary"]["verified_for_retrieval_diagnostics_count"] == 0
    assert gate["summary"]["verification_review_required_count"] == 4
    assert gate["summary"]["verification_blocked_count"] == 2
    assert gate["summary"]["retrieval_use_allowed_by_gate"] is False
    assert gate["summary"]["index_written_by_gate"] is False
    assert gate["summary"]["commit_review_packet_status"] == "commit_review_blocked"
    assert gate["linked_gate_summary"]["legal_rag_embedding_index_commit_review_packet"] == "commit_review_blocked"
    assert gate["post_commit_verification_policy"]["retrieval_diagnostics_review_only"] is True
    assert gate["post_commit_verification_policy"]["index_write_allowed"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["writes_index"] is False


def test_post_commit_verification_gate_maps_success_observation_to_diagnostics_review_only():
    gate = LegalRagEmbeddingIndexPostCommitVerificationGateService().build_gate(
        source_rows=_source_rows(1),
        observation_rows=_ready_observations(1),
        post_commit_observations=_post_commit_success(1),
    )
    row = gate["verification_rows"][0]

    assert gate["status"] == "post_commit_verification_ready"
    assert gate["summary"]["verified_for_retrieval_diagnostics_count"] == 1
    assert gate["summary"]["verification_review_required_count"] == 0
    assert gate["summary"]["verification_blocked_count"] == 0
    assert gate["summary"]["retrieval_diagnostics_review_only_allowed"] is True
    assert row["verification_status"] == "verified_for_retrieval_diagnostics"
    assert row["verification_action"] == "allow_retrieval_diagnostics_review_only"
    assert row["reason_codes"] == ["post_commit_verification_ready_for_diagnostics_review"]
    assert row["privacy_boundary"]["index_written"] is False
    assert row["privacy_boundary"]["retrieval_use_enabled"] is False
    assert "legal-rag-embedding-index-commit-review-packet" in row["linked_gate_ids"]


def test_post_commit_verification_gate_maps_mismatch_and_rollback_to_review_and_block():
    gate = LegalRagEmbeddingIndexPostCommitVerificationGateService().build_gate(
        source_rows=_source_rows(3),
        observation_rows=_ready_observations(3),
        post_commit_observations={
            "post_commit_observations": [
                {
                    "queue_order": 1,
                    "post_commit_status": "success",
                    "observed_vector_slot_count": 1,
                    "observed_index_entry_count": 1,
                    "metadata_record_count": 1,
                    "retrieval_locator_count": 1,
                    "checksum_record_count": 1,
                },
                {
                    "queue_order": 2,
                    "post_commit_status": "success",
                    "observed_vector_slot_count": 1,
                    "observed_index_entry_count": 0,
                    "metadata_record_count": 1,
                    "retrieval_locator_count": 0,
                    "checksum_record_count": 1,
                },
                {
                    "queue_order": 3,
                    "post_commit_status": "failed",
                    "observed_vector_slot_count": 1,
                    "observed_index_entry_count": 1,
                    "metadata_record_count": 1,
                    "retrieval_locator_count": 1,
                    "checksum_record_count": 1,
                    "failed_entry_count": 1,
                    "rollback_required": True,
                },
            ]
        },
    )
    rows = gate["verification_rows"]

    assert gate["status"] == "post_commit_verification_blocked"
    assert gate["summary"]["verified_for_retrieval_diagnostics_count"] == 1
    assert gate["summary"]["verification_review_required_count"] == 1
    assert gate["summary"]["verification_blocked_count"] == 1
    assert rows[0]["verification_status"] == "verified_for_retrieval_diagnostics"
    assert rows[1]["verification_status"] == "verification_review_required"
    assert rows[1]["verification_action"] == "hold_for_post_commit_review"
    assert "observed_index_entry_count_mismatch" in rows[1]["reason_codes"]
    assert "retrieval_locator_count_below_expected" in rows[1]["reason_codes"]
    assert rows[2]["verification_status"] == "verification_blocked"
    assert rows[2]["verification_action"] == "block_retrieval_use_and_prepare_rollback"
    assert rows[2]["rollback_action"] == "prepare_external_rollback_review"
    assert "rollback_required" in rows[2]["reason_codes"]
    assert "failed_index_entries_present" in rows[2]["reason_codes"]
    assert gate["summary"]["retrieval_diagnostics_review_only_allowed"] is False


def test_post_commit_verification_gate_requires_success_like_post_commit_status():
    gate = LegalRagEmbeddingIndexPostCommitVerificationGateService().build_gate(
        source_rows=_source_rows(1),
        observation_rows=_ready_observations(1),
        post_commit_observations={
            "post_commit_observations": {
                "rows": [
                    {
                        "queue_order": 1,
                        "post_commit_status": "not_supplied",
                        "observed_vector_slot_count": 1,
                        "observed_index_entry_count": 1,
                        "metadata_record_count": 1,
                        "retrieval_locator_count": 1,
                        "checksum_record_count": 1,
                    }
                ]
            }
        },
    )
    row = gate["verification_rows"][0]

    assert gate["status"] == "post_commit_verification_review_required"
    assert gate["summary"]["retrieval_diagnostics_review_only_allowed"] is False
    assert row["verification_status"] == "verification_review_required"
    assert "post_commit_status_requires_review:not_supplied" in row["reason_codes"]


def test_post_commit_verification_gate_ignores_unsafe_payload_without_echoing_values():
    secret = "sk-" + ("G" * 24)
    gate = LegalRagEmbeddingIndexPostCommitVerificationGateService().build_gate(
        source_rows=[
            {
                **_source_rows(1)[0],
                "source_id": "do-not-echo-post-commit-source-id",
                "raw_text": "RAW_POST_COMMIT_TEXT",
                "api_key": secret,
                "email": "commit-client@example.invalid",
                "embedding_vector": [0.1, 0.2],
            }
        ],
        observation_rows={
            "observations": [
                {
                    **_ready_observations(1)["observations"][0],
                    "source_id": "do-not-echo-post-commit-source-id",
                    "raw_legal_text": "RAW_POST_COMMIT_TEXT",
                    "api_key": secret,
                    "committer_email": "commit-client@example.invalid",
                    "embedding_vector": [0.1, 0.2],
                }
            ]
        },
        post_commit_observations={
            "post_commit_observations": [
                {
                    **_post_commit_success(1)["post_commit_observations"][0],
                    "source_id": "do-not-echo-post-commit-source-id",
                    "raw_legal_text": "RAW_POST_COMMIT_TEXT",
                    "api_key": secret,
                    "committer_email": "commit-client@example.invalid",
                    "embedding_vectors": [0.1, 0.2],
                }
            ]
        },
    )
    rendered = str(gate)

    assert "source_id" in gate["input_contract"]["forbidden_fields_ignored"]
    assert "committer_email" in gate["input_contract"]["forbidden_fields_ignored"]
    assert gate["input_contract"]["source_id_echoed"] is False
    assert gate["input_contract"]["committer_identity_collected"] is False
    assert "RAW_POST_COMMIT_TEXT" not in rendered
    assert "do-not-echo-post-commit-source-id" not in rendered
    assert "commit-client@example.invalid" not in rendered
    assert secret not in rendered
    assert not SENSITIVE_PATTERN.search(rendered)


def test_post_commit_verification_gate_claim_and_privacy_boundaries_are_safe():
    gate = LegalRagEmbeddingIndexPostCommitVerificationGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["embeddings_created"] is False
    assert gate["summary"]["index_written_by_gate"] is False
    assert gate["claim_boundary"]["maintainer_commit_approval_claimed"] is False
    assert gate["claim_boundary"]["index_commit_executed_by_gate_claimed"] is False
    assert gate["claim_boundary"]["post_commit_success_claimed_without_observation"] is False
    assert gate["claim_boundary"]["automatic_retrieval_enablement_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_approval_item_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_source_chunks"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["returns_committer_identity"] is False
    assert gate["privacy_boundary"]["creates_embeddings"] is False
    assert gate["privacy_boundary"]["writes_index"] is False
    assert gate["privacy_boundary"]["writes_commit_record"] is False


def test_post_commit_verification_gate_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-index-post-commit-verification-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["verification_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-index-post-commit-verification-gate",
        json={
            "source_rows": _source_rows(1),
            **_ready_observations(1),
            **_post_commit_success(1),
        },
    )

    assert reviewed.status_code == 200
    data = reviewed.json()["data"]
    assert data["status"] == "post_commit_verification_ready"
    assert data["verification_rows"][0]["verification_action"] == "allow_retrieval_diagnostics_review_only"
