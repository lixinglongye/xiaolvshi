import re

import pytest

from services.legal_rag_embedding_chunk_policy_gate import LegalRagEmbeddingChunkPolicyGateService


def test_chunk_policy_gate_builds_metadata_only_chunk_plan():
    gate = LegalRagEmbeddingChunkPolicyGateService().build_gate()

    assert gate["id"] == "legal-rag-embedding-chunk-policy-gate"
    assert gate["schema_version"] == "legal-rag-embedding-chunk-policy-gate-v1"
    assert gate["status"] == "blocked"
    assert gate["summary"]["source_row_count"] == 6
    assert gate["summary"]["ready_row_count"] == 2
    assert gate["summary"]["review_row_count"] == 2
    assert gate["summary"]["blocked_row_count"] == 2
    assert gate["summary"]["planned_chunk_total"] == 30
    assert gate["summary"]["estimated_token_total"] == 12760
    assert gate["summary"]["missing_citation_anchor_count"] == 1
    assert gate["summary"]["missing_locator_count"] == 1
    assert gate["summary"]["forbidden_field_row_count"] == 1
    assert gate["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert gate["summary"]["embedding_default_canonical_model"] == "gemini-embedding-001"
    assert gate["linked_gate_summary"]["legal_rag_embedding_readiness_gate"] == "ready_with_blockers"
    assert gate["linked_gate_summary"]["legal_rag_index_coverage_gate"] == "ready_with_blockers"
    assert gate["linked_gate_summary"]["legal_rag_retrieval_diagnostics_gate"] == "ready_with_blockers"
    assert gate["linked_gate_summary"]["legal_source_durable_index_plan"] == "ready"
    assert gate["linked_gate_summary"]["legal_source_ingestion_metadata"] == "blocked"

    assert set(gate["target_chunk_policy"]) >= {"statute", "regulation", "case", "template", "internal_note"}
    assert gate["chunk_policy"]["max_laptop_safe_chunks_per_source"] == 12
    assert gate["chunk_policy"]["requires_retrieval_locator"] is True
    assert gate["chunk_policy"]["embedding_creation_allowed"] is False


def test_chunk_policy_gate_rows_explain_ready_review_and_block_actions():
    gate = LegalRagEmbeddingChunkPolicyGateService().build_gate()
    rows = {row["id"]: row for row in gate["chunk_policy_rows"]}

    statute = rows["chunk-statute-sections-ready"]
    review_due = rows["chunk-regulation-review-due"]
    missing_anchor = rows["chunk-case-anchor-review"]
    locator_block = rows["chunk-missing-locator-block"]
    forbidden_block = rows["chunk-forbidden-field-block"]

    assert statute["chunk_policy_status"] == "ready"
    assert statute["target_chunk_tokens"] == 512
    assert statute["overlap_tokens"] == 64
    assert statute["planned_chunk_count"] == 7
    assert statute["release_action"] == "allow_embedding_chunk_preflight"
    assert statute["reason_codes"] == ["chunk_policy_ready"]
    assert review_due["chunk_policy_status"] == "review_required"
    assert "freshness_requires_review:review_due" in review_due["reason_codes"]
    assert missing_anchor["planned_chunk_count"] == 10
    assert "citation_anchor_missing" in missing_anchor["reason_codes"]
    assert locator_block["chunk_policy_status"] == "blocked"
    assert locator_block["release_action"] == "block_embedding_chunking"
    assert "retrieval_locator_missing" in locator_block["reason_codes"]
    assert forbidden_block["chunk_policy_status"] == "blocked"
    assert "forbidden_field_present" in forbidden_block["reason_codes"]
    assert "raw_text" in forbidden_block["forbidden_fields_present"]
    assert "embedding_vector" in forbidden_block["forbidden_fields_present"]

    for row in gate["chunk_policy_rows"]:
        assert row["embedding_model"] == "gemini-embedding-001"
        assert "legal-rag-embedding-readiness-gate" in row["linked_gate_ids"]
        assert "legal-rag-index-coverage-gate" in row["linked_gate_ids"]
        assert "legal-rag-retrieval-diagnostics-gate" in row["linked_gate_ids"]
        assert "legal-source-durable-index-plan" in row["linked_gate_ids"]
        assert "legal-source-ingestion-metadata" in row["linked_gate_ids"]
        assert row["privacy_boundary"]["source_ids_returned"] is False
        assert row["privacy_boundary"]["raw_legal_text_returned"] is False
        assert row["privacy_boundary"]["source_chunks_returned"] is False
        assert row["privacy_boundary"]["embedding_vectors_returned"] is False
        assert row["privacy_boundary"]["credentials_returned"] is False


def test_chunk_policy_gate_blocks_unsafe_custom_metadata_without_echoing_values():
    secret = "sk-" + ("A" * 24)
    raw_text = "UNSAFE_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK"
    email = "client@example.invalid"
    gate = LegalRagEmbeddingChunkPolicyGateService().build_gate(
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
    row = gate["chunk_policy_rows"][0]
    rendered = str(gate)

    assert gate["status"] == "blocked"
    assert row["id"] == "chunk-policy-row-1-statute"
    assert row["chunk_policy_status"] == "blocked"
    assert row["forbidden_fields_present"] == ["api_key", "embedding_vector", "raw_text", "source_id"]
    assert row["sensitive_value_present"] is True
    assert "forbidden_field_present" in row["reason_codes"]
    assert "sensitive_value_present" in row["reason_codes"]
    assert raw_text not in rendered
    assert secret not in rendered
    assert email not in rendered
    assert "do-not-echo-source-id" not in rendered
    assert re.search(r"sk-[A-Za-z0-9]{20,}", rendered) is None


def test_chunk_policy_gate_claim_and_privacy_boundaries_are_safe():
    gate = LegalRagEmbeddingChunkPolicyGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["index_written"] is False
    assert gate["summary"]["embeddings_created"] is False
    assert gate["summary"]["source_ids_returned"] is False
    assert gate["summary"]["raw_legal_text_included"] is False
    assert gate["summary"]["source_chunks_included"] is False
    assert gate["summary"]["embedding_vectors_included"] is False
    assert gate["claim_boundary"]["chunk_quality_claimed"] is False
    assert gate["claim_boundary"]["embedding_quality_claimed"] is False
    assert gate["claim_boundary"]["index_quality_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_source_chunks"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["creates_embeddings"] is False
    assert gate["privacy_boundary"]["writes_index"] is False
    assert gate["input_contract"]["source_id_echoed"] is False
    assert "source_id" in gate["input_contract"]["forbidden_fields_ignored"]
    assert "chunk_text" in gate["input_contract"]["forbidden_fields_ignored"]
    assert "embedding_vector" in gate["input_contract"]["forbidden_fields_ignored"]


def test_chunk_policy_gate_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-chunk-policy-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["source_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_source_chunks"] is False
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-chunk-policy-gate",
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
    assert data["chunk_policy_rows"][0]["planned_chunk_count"] == 1
    assert data["chunk_policy_rows"][0]["release_action"] == "allow_embedding_chunk_preflight"
