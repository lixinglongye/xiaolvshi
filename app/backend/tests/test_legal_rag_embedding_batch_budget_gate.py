import re

import pytest

from services.legal_rag_embedding_batch_budget_gate import LegalRagEmbeddingBatchBudgetGateService


def test_embedding_batch_budget_gate_builds_metadata_only_budget_plan():
    gate = LegalRagEmbeddingBatchBudgetGateService().build_gate()

    assert gate["id"] == "legal-rag-embedding-batch-budget-gate"
    assert gate["schema_version"] == "legal-rag-embedding-batch-budget-gate-v1"
    assert gate["status"] == "blocked"
    assert gate["summary"]["batch_budget_row_count"] == 6
    assert gate["summary"]["ready_row_count"] == 2
    assert gate["summary"]["review_row_count"] == 2
    assert gate["summary"]["blocked_row_count"] == 2
    assert gate["summary"]["planned_batch_total"] == 7
    assert gate["summary"]["planned_chunk_total"] == 30
    assert gate["summary"]["estimated_token_total"] == 12760
    assert gate["summary"]["estimated_batch_cost_usd"] == 0.000957
    assert gate["summary"]["batch_input_usd_per_million_tokens"] == 0.075
    assert gate["summary"]["embedding_default_model"] == "gemini-embedding-001"
    assert gate["summary"]["dry_run_gate_status"] == "blocked"
    assert gate["summary"]["embedding_preflight_status"] == "review_required"
    assert gate["linked_gate_summary"]["legal_rag_embedding_index_dry_run_gate"] == "blocked"
    assert gate["linked_gate_summary"]["modelops_gemini_embedding_cheap_first_preflight"] == "review_required"
    assert gate["batch_budget_policy"]["max_laptop_safe_chunks_per_batch"] == 8
    assert gate["batch_budget_policy"]["embedding_creation_allowed"] is False
    assert gate["batch_budget_policy"]["model_call_allowed"] is False
    assert gate["batch_budget_policy"]["index_write_allowed"] is False


def test_embedding_batch_budget_rows_map_ready_review_and_blocked_actions():
    gate = LegalRagEmbeddingBatchBudgetGateService().build_gate()
    ready_rows = [row for row in gate["batch_budget_rows"] if row["batch_status"] == "ready"]
    review_rows = [row for row in gate["batch_budget_rows"] if row["batch_status"] == "review_required"]
    blocked_rows = [row for row in gate["batch_budget_rows"] if row["batch_status"] == "blocked"]

    assert len(ready_rows) == 2
    assert len(review_rows) == 2
    assert len(blocked_rows) == 2
    assert all(row["release_action"] == "allow_laptop_embedding_batch_preflight" for row in ready_rows)
    assert all(row["release_action"] == "review_or_split_before_embedding_batch" for row in review_rows)
    assert all(row["release_action"] == "block_embedding_batch" for row in blocked_rows)

    split_rows = [row for row in gate["batch_budget_rows"] if row["planned_batch_count"] > 1]
    assert len(split_rows) == 1
    assert split_rows[0]["source_type"] == "case"
    assert "chunk_count_requires_laptop_safe_batch_split" in split_rows[0]["reason_codes"]

    for row in gate["batch_budget_rows"]:
        assert row["embedding_model"] == "gemini-embedding-001"
        assert row["batch_input_usd_per_million_tokens"] == 0.075
        assert "legal-rag-embedding-index-dry-run-gate" in row["linked_gate_ids"]
        assert "modelops-gemini-embedding-cheap-first-preflight" in row["linked_gate_ids"]
        assert row["privacy_boundary"]["source_ids_returned"] is False
        assert row["privacy_boundary"]["source_chunks_returned"] is False
        assert row["privacy_boundary"]["embedding_vectors_returned"] is False
        assert row["privacy_boundary"]["model_called"] is False
        assert row["privacy_boundary"]["index_written"] is False


def test_embedding_batch_budget_blocks_unsafe_custom_metadata_without_echoing_values():
    secret = "sk-" + ("C" * 24)
    raw_text = "UNSAFE_BATCH_RAW_LEGAL_TEXT_SHOULD_NOT_LEAK"
    email = "batch-client@example.invalid"
    gate = LegalRagEmbeddingBatchBudgetGateService().build_gate(
        [
            {
                "source_type": "template",
                "jurisdiction": "CN-National",
                "freshness_status": "fresh",
                "estimated_token_count": 300,
                "section_count": 2,
                "citation_anchor_count": 1,
                "retrieval_locator_present": True,
                "source_id": "do-not-echo-batch-source-id",
                "raw_text": raw_text,
                "api_key": secret,
                "email": email,
                "embedding_vector": [0.1, 0.2],
            }
        ]
    )
    rendered = str(gate)

    assert gate["status"] == "blocked"
    assert gate["batch_budget_rows"][0]["batch_status"] == "blocked"
    assert "dry_run_row_blocked" in gate["batch_budget_rows"][0]["reason_codes"]
    assert raw_text not in rendered
    assert secret not in rendered
    assert email not in rendered
    assert "do-not-echo-batch-source-id" not in rendered
    assert re.search(r"sk-[A-Za-z0-9]{20,}", rendered) is None


def test_embedding_batch_budget_claim_and_privacy_boundaries_are_safe():
    gate = LegalRagEmbeddingBatchBudgetGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["embeddings_created"] is False
    assert gate["summary"]["index_written"] is False
    assert gate["summary"]["database_written"] is False
    assert gate["claim_boundary"]["embedding_batch_executed_claimed"] is False
    assert gate["claim_boundary"]["index_commit_claimed"] is False
    assert gate["claim_boundary"]["pricing_accuracy_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_source_chunks"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["creates_embeddings"] is False
    assert gate["privacy_boundary"]["writes_index"] is False
    assert gate["privacy_boundary"]["writes_database"] is False
    assert gate["input_contract"]["source_id_echoed"] is False
    assert gate["input_contract"]["budget_only"] is True
    assert "source_id" in gate["input_contract"]["forbidden_fields_ignored"]


def test_embedding_batch_budget_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-batch-budget-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["batch_budget_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_source_chunks"] is False
    assert payload["data"]["privacy_boundary"]["returns_embedding_vectors"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-batch-budget-gate",
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
    assert data["batch_budget_rows"][0]["planned_batch_count"] == 1
    assert data["batch_budget_rows"][0]["release_action"] == "allow_laptop_embedding_batch_preflight"
