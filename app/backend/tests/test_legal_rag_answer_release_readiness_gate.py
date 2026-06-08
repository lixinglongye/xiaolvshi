import re

import pytest

from services.legal_rag_answer_release_readiness_gate import LegalRagAnswerReleaseReadinessGateService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|RAW_QUERY_SHOULD_NOT_LEAK|RAW_CONTEXT_SHOULD_NOT_LEAK|"
    r"RAW_LEGAL_TEXT_SHOULD_NOT_LEAK|client@example\.invalid|SRC-CONTRACT-1|SRC-UNKNOWN-1"
)


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
                "retrieved_context": "RAW_CONTEXT_SHOULD_NOT_LEAK",
                "client_email": "client@example.invalid",
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
                "raw_legal_text": "RAW_LEGAL_TEXT_SHOULD_NOT_LEAK",
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


def test_answer_release_readiness_scores_ready_review_and_blocked_rows_without_raw_payloads():
    gate = LegalRagAnswerReleaseReadinessGateService().build_gate(_sample_observations())
    rows = {row["id"]: row for row in gate["answer_release_rows"]}
    serialized = str(gate)

    assert gate["id"] == "legal-rag-answer-release-readiness-gate"
    assert gate["schema_version"] == "legal-rag-answer-release-readiness-gate-v1"
    assert gate["status"] == "blocked"
    assert gate["summary"]["answer_release_row_count"] == 3
    assert gate["summary"]["ready_answer_count"] == 1
    assert gate["summary"]["review_required_count"] == 1
    assert gate["summary"]["blocked_answer_count"] == 1
    assert gate["summary"]["internal_draft_allowed_count"] == 1
    assert gate["summary"]["citation_packet_required_count"] == 2
    assert gate["summary"]["lawyer_review_required_count"] == 2
    assert gate["summary"]["client_delivery_allowed_count"] == 0

    assert rows["obs-ready"]["answer_release_status"] == "ready"
    assert rows["obs-ready"]["answer_release_action"] == "prepare_internal_answer_draft_with_citation_packet"
    assert rows["obs-ready"]["internal_answer_draft_allowed"] is True
    assert rows["obs-ready"]["client_delivery_allowed"] is False
    assert rows["obs-ready"]["reason_codes"] == ["answer_release_ready"]

    assert rows["obs-review"]["answer_release_status"] == "review_required"
    assert rows["obs-review"]["answer_release_action"] == "require_lawyer_review_before_answer_release"
    assert "answer_release:review_required" in rows["obs-review"]["reason_codes"]
    assert "jurisdiction:mismatch" in rows["obs-review"]["reason_codes"]
    assert rows["obs-review"]["lawyer_review_required"] is True

    assert rows["obs-blocked"]["answer_release_status"] == "blocked"
    assert rows["obs-blocked"]["answer_release_action"] == "block_answer_release"
    assert "answer_release:blocked" in rows["obs-blocked"]["reason_codes"]
    assert rows["obs-blocked"]["internal_answer_draft_allowed"] is False

    assert gate["answer_release_status_counts"] == {"blocked": 1, "ready": 1, "review_required": 1}
    assert gate["answer_release_action_counts"]["block_answer_release"] == 1
    assert gate["answer_release_policy"]["allows_client_delivery"] is False
    assert gate["answer_release_policy"]["allows_legal_advice_claim"] is False
    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_source_ids"] is False
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_retrieved_context"] is False
    assert gate["privacy_boundary"]["sends_client_delivery"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_answer_release_readiness_accepts_direct_observation_rows_without_reinterpreting_raw_payloads():
    gate = LegalRagAnswerReleaseReadinessGateService().build_gate(
        {
            "observation_rows": [
                {
                    "id": "direct-ready",
                    "query_intent": "statute_check",
                    "retrieval_status": "ready",
                    "release_action": "allow_retrieval_use",
                    "source_coverage_status": "ready",
                    "top_k_depth_status": "sufficient",
                    "jurisdiction_status": "matched",
                    "freshness_status": "fresh",
                    "cheap_first_action": {"decision": "continue", "starts_cheap": True},
                    "source_ids": ["SRC-SHOULD-NOT-LEAK"],
                    "question": "RAW_QUERY_SHOULD_NOT_LEAK",
                }
            ]
        }
    )

    assert gate["status"] == "ready"
    assert gate["summary"]["ready_answer_count"] == 1
    assert gate["answer_release_rows"][0]["id"] == "direct-ready"
    assert gate["answer_release_rows"][0]["answer_release_status"] == "ready"
    assert "SRC-SHOULD-NOT-LEAK" not in str(gate)
    assert "RAW_QUERY_SHOULD_NOT_LEAK" not in str(gate)


def test_answer_release_readiness_empty_payload_is_not_run_and_never_claims_external_work():
    gate = LegalRagAnswerReleaseReadinessGateService().build_gate()

    assert gate["status"] == "not_run"
    assert gate["summary"]["answer_release_row_count"] == 0
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["summary"]["gemini_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["legal_advice_claimed"] is False
    assert gate["claim_boundary"]["automatic_client_delivery_claimed"] is False
    assert gate["recommended_actions"] == [
        "Submit sanitized retrieval observations before claiming answer release readiness."
    ]


def test_answer_release_readiness_route_get_and_post_return_metadata_only_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-rag-answer-release-readiness-gate")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "not_run"

    post_response = client.post(
        "/api/v1/maintenance/legal-rag-answer-release-readiness-gate",
        json=_sample_observations(),
    )

    assert post_response.status_code == 200
    payload = post_response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "blocked"
    assert payload["data"]["summary"]["answer_release_row_count"] == 3
    assert payload["data"]["privacy_boundary"]["returns_source_ids"] is False
