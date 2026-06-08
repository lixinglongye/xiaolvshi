import re

import pytest

from services.legal_rag_embedding_index_dry_run_gate import LegalRagEmbeddingIndexDryRunGateService


def test_embedding_index_dry_run_gate_builds_metadata_only_manifest():
    gate = LegalRagEmbeddingIndexDryRunGateService().build_gate()

    assert gate["id"] == "legal-rag-embedding-index-dry-run-gate"
    assert gate["schema_version"] == "legal-rag-embedding-index-dry-run-gate-v1"
    assert gate["status"] == "blocked"
    assert gate["summary"]["dry_run_row_count"] == 6
    assert gate["summary"]["manifest_ready_row_count"] == 2
    assert gate["summary"]["review_row_count"] == 2
    assert gate["summary"]["blocked_row_count"] == 2
    assert gate["summary"]["planned_chunk_total"] == 30
    assert gate["summary"]["planned_vector_slot_total"] == 30
    assert gate["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert gate["summary"]["embedding_default_canonical_model"] == "gemini-embedding-001"
    assert gate["summary"]["chunk_policy_gate_status"] == "blocked"
    assert gate["summary"]["durable_index_plan_status"] == "ready"
    assert gate["linked_gate_summary"]["legal_rag_embedding_chunk_policy_gate"] == "blocked"
    assert gate["linked_gate_summary"]["legal_source_index_repository"] == "validates_before_upsert"
    assert gate["dry_run_policy"]["embedding_creation_allowed"] is False
    assert gate["dry_run_policy"]["index_write_allowed"] is False
    assert gate["dry_run_policy"]["database_write_allowed"] is False


def test_embedding_index_dry_run_rows_map_ready_review_and_blocked_chunk_policy():
    gate = LegalRagEmbeddingIndexDryRunGateService().build_gate()
    ready_rows = [row for row in gate["dry_run_rows"] if row["dry_run_status"] == "ready"]
    review_rows = [row for row in gate["dry_run_rows"] if row["dry_run_status"] == "review_required"]
    blocked_rows = [row for row in gate["dry_run_rows"] if row["dry_run_status"] == "blocked"]

    assert len(ready_rows) == 2
    assert len(review_rows) == 2
    assert len(blocked_rows) == 2
    assert all(row["commit_action"] == "allow_manifest_review_only" for row in ready_rows)
    assert all(row["commit_action"] == "review_before_index_manifest" for row in review_rows)
    assert all(row["commit_action"] == "block_index_write" for row in blocked_rows)

    for row in gate["dry_run_rows"]:
        assert row["planned_vector_slot_count"] == row["planned_chunk_count"]
        assert row["embedding_model"] == "gemini-embedding-001"
        assert "metadata_hash_required" in row["manifest_fields"]
        assert "legal-rag-embedding-chunk-policy-gate" in row["linked_gate_ids"]
        assert "legal-source-index-repository" in row["linked_gate_ids"]
        assert row["privacy_boundary"]["source_ids_returned"] is False
        assert row["privacy_boundary"]["source_chunks_returned"] is False
        assert row["privacy_boundary"]["embedding_vectors_returned"] is False
        assert row["privacy_boundary"]["database_written"] is False
        assert row["privacy_boundary"]["index_written"] is False


def test_embedding_index_dry_run_blocks_unsafe_custom_metadata_without_echoing_values():
    secret = "sk-" + ("B" * 24)
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK"
    email = "client@example.invalid"
    gate = LegalRagEmbeddingIndexDryRunGateService().build_gate(
        [
            {
                "source_type": "statute",
                "jurisdiction": "CN-National",
                "freshness_status": "fresh",
                "estimated_token_count": 512,
                "section_count": 1,
                "citation_anchor_count": 1,
                "retrieval_locator_present": True,
                "source_id": "do-not-echo-source-id",
                "raw_text": raw_text,
                "api_key": secret,
                "contact": email,
                "embedding_vector": [0.1, 0.2],
            }
        ]
    )
    rendered = str(gate)

    assert gate["status"] == "blocked"
    assert gate["dry_run_rows"][0]["dry_run_status"] == "blocked"
    assert "chunk_policy_blocked" in gate["dry_run_rows"][0]["reason_codes"]
    assert raw_text not in rendered
    assert secret not in rendered
    assert email not in rendered
    assert "do-not-echo-source-id" not in rendered
    assert re.search(r"sk-[A-Za-z0-9]{20,}", rendered) is None


def test_embedding_index_dry_run_claim_and_privacy_boundaries_are_safe():
    gate = LegalRagEmbeddingIndexDryRunGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["embeddings_created"] is False
    assert gate["summary"]["index_written"] is False
    assert gate["summary"]["database_written"] is False
    assert gate["summary"]["source_ids_returned"] is False
    assert gate["summary"]["raw_legal_text_included"] is False
    assert gate["summary"]["source_chunks_included"] is False
    assert gate["summary"]["embedding_vectors_included"] is False
    assert gate["claim_boundary"]["index_commit_claimed"] is False
    assert gate["claim_boundary"]["vector_store_quality_claimed"] is False
    assert gate["claim_boundary"]["automatic_index_write_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_source_chunks"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["creates_embeddings"] is False
    assert gate["privacy_boundary"]["writes_index"] is False
    assert gate["privacy_boundary"]["writes_database"] is False
    assert gate["input_contract"]["source_id_echoed"] is False
    assert "source_id" in gate["input_contract"]["forbidden_fields_ignored"]
    assert "embedding_vector" in gate["input_contract"]["forbidden_fields_ignored"]


def test_embedding_index_dry_run_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-index-dry-run-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["dry_run_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_source_chunks"] is False
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-index-dry-run-gate",
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
    assert data["status"] == "ready"
    assert data["dry_run_rows"][0]["planned_chunk_count"] == 1
    assert data["dry_run_rows"][0]["commit_action"] == "allow_manifest_review_only"
