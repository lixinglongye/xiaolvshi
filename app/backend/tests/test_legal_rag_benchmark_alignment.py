import re

import pytest

from services.legal_rag_benchmark_alignment import LegalRagBenchmarkAlignmentService


def test_legal_rag_benchmark_alignment_maps_public_signals_to_local_gates():
    scorecard = LegalRagBenchmarkAlignmentService().build_scorecard()

    assert scorecard["id"] == "legal-rag-benchmark-alignment"
    assert scorecard["status"] == "ready_with_blockers"
    assert scorecard["summary"]["dimension_count"] == 4
    assert scorecard["summary"]["benchmark_signal_count"] == 4
    assert scorecard["summary"]["diagnostic_row_count"] >= 6
    assert scorecard["summary"]["retrieval_blocked_row_count"] >= 1
    assert scorecard["summary"]["abstention_blocker_count"] >= 1
    assert scorecard["summary"]["public_sampler_source_count"] >= 7
    assert scorecard["summary"]["fixture_crosswalk_gap_count"] >= 1
    assert scorecard["summary"]["cheap_first_default"] is True

    row_ids = {row["id"] for row in scorecard["alignment_rows"]}
    assert {
        "legal-rag-source-coverage",
        "corrective-rag-abstention",
        "chinese-legal-rag-transfer",
        "contract-rag-clause-grounding",
    } <= row_ids


def test_legal_rag_benchmark_alignment_rows_block_claims_for_gaps():
    scorecard = LegalRagBenchmarkAlignmentService().build_scorecard()
    rows = {row["id"]: row for row in scorecard["alignment_rows"]}

    source_coverage = rows["legal-rag-source-coverage"]
    corrective = rows["corrective-rag-abstention"]
    chinese = rows["chinese-legal-rag-transfer"]

    assert source_coverage["release_action"] == "block_claims"
    assert "retrieval_diagnostic_blockers_present" in source_coverage["gap_reasons"]
    assert "legal-rag-retrieval-diagnostics-gate" in source_coverage["linked_gate_ids"]
    assert "legal-rag-authority-citation-gate" in source_coverage["linked_gate_ids"]
    assert source_coverage["premium_exception_allowed"] is False
    assert source_coverage["starts_cheap"] is False
    assert corrective["gate_statuses"]["legal-rag-abstention-escalation-gate"] == "ready_with_blockers"
    assert "public_source_catalog_only" in corrective["gap_reasons"]
    assert chinese["coverage_score"] >= 80
    assert chinese["public_source_sampling_states"]["lexeval"] == "license_review_required"

    for row in scorecard["alignment_rows"]:
        assert row["privacy_boundary"]["public_benchmark_text_returned"] is False
        assert row["privacy_boundary"]["retrieved_context_returned"] is False
        assert row["privacy_boundary"]["raw_legal_text_returned"] is False
        assert row["privacy_boundary"]["model_output_returned"] is False


def test_legal_rag_benchmark_alignment_claim_and_privacy_boundaries_are_explicit():
    scorecard = LegalRagBenchmarkAlignmentService().build_scorecard()

    assert scorecard["summary"]["model_called"] is False
    assert scorecard["summary"]["gateway_called"] is False
    assert scorecard["summary"]["newapi_called"] is False
    assert scorecard["summary"]["network_called"] is False
    assert scorecard["summary"]["dataset_downloaded"] is False
    assert scorecard["summary"]["raw_public_benchmark_text_included"] is False
    assert scorecard["claim_boundary"]["legal_advice_claimed"] is False
    assert scorecard["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert scorecard["claim_boundary"]["leaderboard_claimed"] is False
    assert scorecard["privacy_boundary"]["metadata_only"] is True
    assert scorecard["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert scorecard["privacy_boundary"]["returns_raw_query"] is False
    assert scorecard["privacy_boundary"]["returns_retrieved_context"] is False
    assert scorecard["privacy_boundary"]["returns_credentials"] is False

    text = str(scorecard)
    assert "UNSAFE_PUBLIC_BENCHMARK_TEXT_SHOULD_NOT_LEAK" not in text
    assert "Can the claimant still file" not in text
    assert "The claimant can still file" not in text
    assert re.search(r"sk-[A-Za-z0-9]{20,}", text) is None


def test_legal_rag_benchmark_alignment_route_returns_scorecard():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/legal-rag-benchmark-alignment")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "legal-rag-benchmark-alignment"
    assert payload["data"]["summary"]["dimension_count"] == 4
    assert payload["data"]["privacy_boundary"]["returns_public_benchmark_text"] is False
