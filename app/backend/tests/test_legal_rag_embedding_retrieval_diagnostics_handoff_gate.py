import re

import pytest

from services.legal_rag_embedding_retrieval_diagnostics_handoff_gate import (
    LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|handoff-client@example.invalid|RAW_HANDOFF_TEXT|do-not-echo-handoff-source-id"
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


def test_handoff_gate_defaults_to_blocked_metadata_only_handoff():
    gate = LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService().build_gate()

    assert gate["id"] == "legal-rag-embedding-retrieval-diagnostics-handoff-gate"
    assert gate["schema_version"] == "legal-rag-embedding-retrieval-diagnostics-handoff-gate-v1"
    assert gate["status"] == "retrieval_diagnostics_handoff_blocked"
    assert gate["summary"]["handoff_row_count"] == 6
    assert gate["summary"]["ready_handoff_count"] == 0
    assert gate["summary"]["hold_handoff_count"] == 4
    assert gate["summary"]["blocked_handoff_count"] == 2
    assert gate["summary"]["production_retrieval_allowed_count"] == 0
    assert gate["summary"]["production_retrieval_allowed_by_gate"] is False
    assert gate["summary"]["query_payload_included"] is False
    assert gate["linked_gate_summary"]["legal_rag_embedding_index_post_commit_verification_gate"] == "post_commit_verification_blocked"
    assert gate["handoff_policy"]["allows_retrieval_diagnostics_review_only"] is True
    assert gate["handoff_policy"]["allows_production_retrieval"] is False
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False


def test_handoff_gate_maps_verified_post_commit_row_to_metadata_only_handoff():
    gate = LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService().build_gate(
        source_rows=_source_rows(1),
        observation_rows=_ready_observations(1),
        post_commit_observations=_post_commit_success(1),
    )
    row = gate["handoff_rows"][0]

    assert gate["status"] == "retrieval_diagnostics_handoff_ready"
    assert gate["summary"]["ready_handoff_count"] == 1
    assert gate["summary"]["hold_handoff_count"] == 0
    assert gate["summary"]["blocked_handoff_count"] == 0
    assert row["handoff_status"] == "ready_for_retrieval_diagnostics_handoff"
    assert row["handoff_action"] == "prepare_metadata_only_retrieval_diagnostics_review"
    assert row["retrieval_diagnostics_review_allowed"] is True
    assert row["production_retrieval_allowed"] is False
    assert row["retrieval_query_allowed"] is False
    assert row["reason_codes"] == ["retrieval_diagnostics_handoff_ready_metadata_only"]
    assert "legal-rag-retrieval-diagnostics-gate" in row["linked_gate_ids"]


def test_handoff_gate_maps_review_and_rollback_rows_to_hold_and_block():
    gate = LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService().build_gate(
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
    rows = gate["handoff_rows"]

    assert gate["status"] == "retrieval_diagnostics_handoff_blocked"
    assert gate["summary"]["ready_handoff_count"] == 1
    assert gate["summary"]["hold_handoff_count"] == 1
    assert gate["summary"]["blocked_handoff_count"] == 1
    assert rows[0]["handoff_status"] == "ready_for_retrieval_diagnostics_handoff"
    assert rows[1]["handoff_status"] == "hold_for_post_commit_review"
    assert rows[1]["handoff_action"] == "hold_retrieval_diagnostics_handoff"
    assert "observed_index_entry_count_mismatch" in rows[1]["reason_codes"]
    assert "post_commit_verification_requires_handoff_review" in rows[1]["reason_codes"]
    assert rows[2]["handoff_status"] == "blocked_until_verification_ready"
    assert rows[2]["handoff_action"] == "block_handoff_and_prepare_rollback_review"
    assert rows[2]["rollback_action"] == "route_to_external_rollback_review"
    assert "rollback_required" in rows[2]["reason_codes"]
    assert "post_commit_verification_blocks_handoff" in rows[2]["reason_codes"]


def test_handoff_gate_ignores_unsafe_payload_without_echoing_values():
    secret = "sk-" + ("H" * 24)
    gate = LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService().build_gate(
        source_rows=[
            {
                **_source_rows(1)[0],
                "source_id": "do-not-echo-handoff-source-id",
                "raw_text": "RAW_HANDOFF_TEXT",
                "api_key": secret,
                "email": "handoff-client@example.invalid",
                "embedding_vector": [0.1, 0.2],
            }
        ],
        observation_rows={
            "observations": [
                {
                    **_ready_observations(1)["observations"][0],
                    "source_id": "do-not-echo-handoff-source-id",
                    "raw_legal_text": "RAW_HANDOFF_TEXT",
                    "api_key": secret,
                    "committer_email": "handoff-client@example.invalid",
                    "embedding_vector": [0.1, 0.2],
                }
            ]
        },
        post_commit_observations={
            "post_commit_observations": {
                "rows": [
                    {
                        **_post_commit_success(1)["post_commit_observations"][0],
                        "source_id": "do-not-echo-handoff-source-id",
                        "raw_query": "RAW_HANDOFF_TEXT",
                        "retrieved_context": "RAW_HANDOFF_TEXT",
                        "api_key": secret,
                        "handoff_client": "handoff-client@example.invalid",
                        "embedding_vectors": [0.1, 0.2],
                    }
                ]
            }
        },
    )
    rendered = str(gate)

    assert "source_id" in gate["input_contract"]["forbidden_fields_ignored"]
    assert "retrieved_context" in gate["input_contract"]["forbidden_fields_ignored"]
    assert gate["input_contract"]["source_id_echoed"] is False
    assert gate["input_contract"]["query_payload_collected"] is False
    assert "RAW_HANDOFF_TEXT" not in rendered
    assert "do-not-echo-handoff-source-id" not in rendered
    assert "handoff-client@example.invalid" not in rendered
    assert secret not in rendered
    assert not SENSITIVE_PATTERN.search(rendered)


def test_handoff_gate_accepts_direct_verification_rows_without_reinterpreting_them():
    gate = LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService().build_gate(
        verification_gate={
            "status": "post_commit_verification_ready",
            "verification_rows": [
                {
                    "source_type": "template",
                    "queue_order": 1,
                    "verification_status": "verified_for_retrieval_diagnostics",
                    "verification_action": "allow_retrieval_diagnostics_review_only",
                    "post_commit_status": "success",
                    "expected_index_entry_count": 1,
                    "observed_index_entry_count": 1,
                    "metadata_record_count": 1,
                    "retrieval_locator_count": 1,
                    "checksum_record_count": 1,
                    "failed_entry_count": 0,
                    "rollback_required": False,
                    "reason_codes": ["post_commit_verification_ready_for_diagnostics_review"],
                }
            ],
        },
    )
    row = gate["handoff_rows"][0]

    assert gate["status"] == "retrieval_diagnostics_handoff_ready"
    assert gate["summary"]["post_commit_verification_gate_status"] == "post_commit_verification_ready"
    assert row["handoff_status"] == "ready_for_retrieval_diagnostics_handoff"
    assert row["handoff_action"] == "prepare_metadata_only_retrieval_diagnostics_review"
    assert row["reason_codes"] == ["retrieval_diagnostics_handoff_ready_metadata_only"]


def test_handoff_gate_claim_and_privacy_boundaries_are_safe():
    gate = LegalRagEmbeddingRetrievalDiagnosticsHandoffGateService().build_gate()

    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["index_written"] is False
    assert gate["claim_boundary"]["retrieval_diagnostics_executed_claimed"] is False
    assert gate["claim_boundary"]["production_retrieval_enabled_claimed"] is False
    assert gate["claim_boundary"]["index_quality_claimed"] is False
    assert gate["claim_boundary"]["retrieval_quality_claimed"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_retrieved_context"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_source_chunks"] is False
    assert gate["privacy_boundary"]["returns_embedding_vectors"] is False
    assert gate["privacy_boundary"]["enables_production_retrieval"] is False
    assert gate["privacy_boundary"]["calls_model"] is False


def test_handoff_gate_route_returns_and_evaluates_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-embedding-retrieval-diagnostics-handoff-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["handoff_row_count"] == 6
    assert payload["data"]["privacy_boundary"]["returns_raw_query"] is False

    reviewed = client.post(
        "/api/v1/maintenance/legal-rag-embedding-retrieval-diagnostics-handoff-gate",
        json={
            "source_rows": _source_rows(1),
            **_ready_observations(1),
            **_post_commit_success(1),
        },
    )

    assert reviewed.status_code == 200
    data = reviewed.json()["data"]
    assert data["status"] == "retrieval_diagnostics_handoff_ready"
    assert data["handoff_rows"][0]["handoff_action"] == "prepare_metadata_only_retrieval_diagnostics_review"

    direct = client.post(
        "/api/v1/maintenance/legal-rag-embedding-retrieval-diagnostics-handoff-gate",
        json={
            "verification_rows": [
                {
                    "source_type": "template",
                    "queue_order": 1,
                    "verification_status": "verified_for_retrieval_diagnostics",
                    "verification_action": "allow_retrieval_diagnostics_review_only",
                    "post_commit_status": "success",
                    "expected_index_entry_count": 1,
                    "observed_index_entry_count": 1,
                    "metadata_record_count": 1,
                    "retrieval_locator_count": 1,
                    "checksum_record_count": 1,
                    "failed_entry_count": 0,
                    "rollback_required": False,
                }
            ]
        },
    )

    assert direct.status_code == 200
    direct_data = direct.json()["data"]
    assert direct_data["status"] == "retrieval_diagnostics_handoff_ready"
    assert direct_data["handoff_rows"][0]["post_commit_verification_status"] == "verified_for_retrieval_diagnostics"
