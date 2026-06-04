import json

import pytest

from services.legal_document_coverage_claim_policy import LegalDocumentCoverageClaimPolicyService


PRIVATE_EMAIL = "coverage-claim@example.test"
PRIVATE_KEY = "sk-PRIVATE_COVERAGE_CLAIM_KEY_SHOULD_NOT_LEAK"


def test_legal_document_coverage_claim_policy_allows_scoped_local_fixture_claims():
    result = LegalDocumentCoverageClaimPolicyService().evaluate(
        [
            "Repository tests include synthetic local fixtures for civil complaint, lawyer letter, contract review, evidence catalog, settlement agreement, and legal opinion coverage.",
        ]
    )

    assert result["status"] == "ready"
    assert result["coverage_summary"]["coverage_status"] == "ready"
    assert result["coverage_summary"]["covered_document_type_count"] == 6
    assert result["coverage_summary"]["missing_document_type_count"] == 0
    assert result["summary"]["ready_count"] == 1
    assert result["summary"]["supported_type_claim_count"] == 1
    assert set(result["claim_checks"][0]["matched_document_types"]) == {
        "civil_complaint",
        "lawyer_letter",
        "contract_review",
        "evidence_catalog",
        "settlement_agreement",
        "legal_opinion",
    }
    assert result["privacy_boundary"]["raw_claim_text_included"] is False


def test_legal_document_coverage_claim_policy_requires_local_scope_for_support_claims():
    result = LegalDocumentCoverageClaimPolicyService().evaluate(["We support legal opinion and settlement agreement workflows."])

    assert result["status"] == "review_required"
    assert result["summary"]["review_required_count"] == 1
    assert result["claim_checks"][0]["reason_codes"] == ["local_evidence_scope_missing"]
    assert result["claim_checks"][0]["unsupported_document_types"] == []


def test_legal_document_coverage_claim_policy_blocks_broad_and_unsupported_claims_without_echo():
    claim = (
        "We support all legal documents, appeal brief drafting, real client documents, "
        f"LegalBench leaderboard claims, and contact {PRIVATE_EMAIL} using {PRIVATE_KEY}."
    )
    result = LegalDocumentCoverageClaimPolicyService().evaluate([claim])
    rendered = json.dumps(result, ensure_ascii=False)
    reasons = set(result["claim_checks"][0]["reason_codes"])

    assert result["status"] == "blocked"
    assert "broad_coverage_claim" in reasons
    assert "unsupported_document_type_claim" in reasons
    assert "real_client_or_production_claim" in reasons
    assert "public_benchmark_claim" in reasons
    assert "sensitive_material_dropped" in reasons
    assert "appeal_brief" in result["claim_checks"][0]["unsupported_document_types"]
    assert claim not in rendered
    assert PRIVATE_EMAIL not in rendered
    assert PRIVATE_KEY not in rendered


def test_legal_document_coverage_claim_policy_handles_chinese_document_type_aliases():
    result = LegalDocumentCoverageClaimPolicyService().evaluate(
        ["\u4ed3\u5e93\u672c\u5730\u5408\u6210 fixture \u8986\u76d6\u6c11\u4e8b\u8d77\u8bc9\u72b6\u3001\u8bc1\u636e\u76ee\u5f55\u548c\u6cd5\u5f8b\u610f\u89c1\u4e66\u3002"]
    )

    assert result["status"] == "ready"
    assert set(result["claim_checks"][0]["matched_document_types"]) == {
        "civil_complaint",
        "evidence_catalog",
        "legal_opinion",
    }


def test_legal_document_coverage_claim_policy_route_is_metadata_only():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/document-coverage/claims",
        json={"claims": [f"All legal documents are covered, email {PRIVATE_EMAIL}"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["status"] == "blocked"
    assert "broad_coverage_claim" in data["claim_checks"][0]["reason_codes"]
    assert PRIVATE_EMAIL not in response.text
