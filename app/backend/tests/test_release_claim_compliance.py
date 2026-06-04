import json

import pytest

from services.release_claim_compliance import ReleaseClaimComplianceService


PRIVATE_EMAIL = "release-claim@example.test"
PRIVATE_KEY = "sk-PRIVATE_CLAIM_KEY_SHOULD_NOT_LEAK"


def test_release_claim_compliance_allows_repository_backed_claims():
    result = ReleaseClaimComplianceService().evaluate(
        [
            "The repository includes backend tests, frontend type checks, release readiness evidence, and maintenance documentation.",
        ]
    )

    assert result["status"] == "ready"
    assert result["summary"]["ready_count"] == 1
    assert result["claim_checks"][0]["reason_codes"] == []
    assert result["privacy_boundary"]["raw_claim_text_included"] is False


def test_release_claim_compliance_blocks_unsupported_public_claims_without_echo():
    claim = (
        "We have thousands of users, a LegalBench score, webhook verified payments, "
        f"and contact {PRIVATE_EMAIL} with {PRIVATE_KEY}."
    )
    result = ReleaseClaimComplianceService().evaluate([claim])
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "blocked"
    reasons = set(result["claim_checks"][0]["reason_codes"])
    assert "external_adoption_claim" in reasons
    assert "public_benchmark_score_claim" in reasons
    assert "payment_provider_settlement_claim" in reasons
    assert "sensitive_material_dropped" in reasons
    assert claim not in rendered
    assert PRIVATE_EMAIL not in rendered
    assert PRIVATE_KEY not in rendered


def test_release_claim_compliance_route_is_metadata_only():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post(
        "/api/v1/maintenance/compliance/release-claims",
        json={"claims": [f"LegalBench score is top tier, email {PRIVATE_EMAIL}"]},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "blocked"
    assert "public_benchmark_score_claim" in data["claim_checks"][0]["reason_codes"]
    assert PRIVATE_EMAIL not in response.text
