import re

import pytest

from services.legal_rag_retrieval_observation_gate import LegalRagRetrievalObservationGateService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|client@example.com|RAW_QUERY_SHOULD_NOT_LEAK|RAW_CONTEXT")


def _sample_observations():
    return {
        "retrieval_observations": [
            {
                "id": "obs-ready",
                "query_intent": "contract_primary_authority",
                "expected_source_count": 2,
                "selected_source_ids": ["SRC-CONTRACT-1", "SRC-CONTRACT-2"],
                "citation_source_ids": ["SRC-CONTRACT-1", "SRC-CONTRACT-2"],
                "top_k_depth": 4,
                "jurisdiction_match": True,
                "freshness_status": "fresh",
                "query": "RAW_QUERY_SHOULD_NOT_LEAK",
                "retrieved_context": "RAW_CONTEXT",
            },
            {
                "id": "obs-review",
                "query_intent": "local_rule_review_due",
                "expected_source_count": 3,
                "selected_source_ids": ["SRC-LOCAL-1", "SRC-LOCAL-2"],
                "citation_source_ids": ["SRC-LOCAL-1", "SRC-LOCAL-2"],
                "top_k_depth": 2,
                "jurisdiction_match": False,
                "freshness_status": "review_due",
                "signals": ["weak_citations"],
            },
            {
                "id": "obs-blocked",
                "query_intent": "empty_index_coverage",
                "expected_source_count": 2,
                "selected_source_ids": [],
                "citation_source_ids": ["SRC-UNKNOWN-1"],
                "top_k_depth": 0,
                "jurisdiction_match": False,
                "freshness_status": "unknown",
                "unknown_source_ids": ["SRC-UNKNOWN-1"],
                "retrieval_gap": True,
            },
        ]
    }


def test_retrieval_observation_gate_scores_ready_review_and_blocked_rows_without_echoing_raw_inputs():
    gate = LegalRagRetrievalObservationGateService().build_gate(_sample_observations())
    serialized = str(gate)
    rows = {row["id"]: row for row in gate["observation_rows"]}

    assert gate["id"] == "legal-rag-retrieval-observation-gate"
    assert gate["status"] == "blocked"
    assert gate["summary"]["observation_row_count"] == 3
    assert gate["summary"]["ready_row_count"] == 1
    assert gate["summary"]["review_row_count"] == 1
    assert gate["summary"]["blocked_row_count"] == 1
    assert gate["summary"]["top_k_gap_count"] == 2
    assert gate["summary"]["jurisdiction_gap_count"] == 2
    assert gate["summary"]["freshness_gap_count"] == 2
    assert gate["summary"]["cheap_first_verify_or_escalate_count"] >= 1

    assert rows["obs-ready"]["retrieval_status"] == "ready"
    assert rows["obs-ready"]["release_action"] == "allow_retrieval_use"
    assert rows["obs-ready"]["cheap_first_action"]["decision"] == "continue"
    assert rows["obs-review"]["retrieval_status"] == "review_required"
    assert rows["obs-review"]["release_action"] == "review_before_answer"
    assert "top_k_depth:shallow" in rows["obs-review"]["reason_codes"]
    assert "jurisdiction:mismatch" in rows["obs-review"]["reason_codes"]
    assert rows["obs-blocked"]["retrieval_status"] == "blocked"
    assert rows["obs-blocked"]["release_action"] == "block_answer_release"
    assert "missing_selected_source_context" in rows["obs-blocked"]["source_validation_reason_codes"]
    assert rows["obs-blocked"]["cheap_first_action"]["requires_operator_review"] is True

    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_retrieved_context"] is False
    assert all(row["privacy_boundary"]["source_ids_returned"] is False for row in gate["observation_rows"])
    assert "SRC-CONTRACT-1" not in serialized
    assert "SRC-UNKNOWN-1" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_retrieval_observation_gate_not_run_for_empty_payload_and_never_claims_external_work():
    gate = LegalRagRetrievalObservationGateService().build_gate()

    assert gate["status"] == "not_run"
    assert gate["summary"]["observation_row_count"] == 0
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["dataset_downloaded"] is False
    assert gate["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert gate["claim_boundary"]["live_gateway_quality_claimed"] is False
    assert gate["recommended_actions"] == [
        "Submit sanitized retrieval observations before claiming Legal RAG retrieval readiness."
    ]


def test_retrieval_observation_gate_route_returns_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post("/api/v1/maintenance/legal-rag-retrieval-observation-gate", json=_sample_observations())

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "blocked"
    assert payload["data"]["summary"]["observation_row_count"] == 3
    assert payload["data"]["privacy_boundary"]["returns_source_ids"] is False
