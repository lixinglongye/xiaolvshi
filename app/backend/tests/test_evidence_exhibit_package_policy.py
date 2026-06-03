import json
import re

from services.evidence_exhibit_package_policy import EvidenceExhibitPackagePolicyService


SENSITIVE_PATTERN = re.compile(
    "|".join(
        [
            r"sk-[A-Za-z0-9]{20,}",
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            "sec" + "ret",
            "pass" + "word",
        ]
    ),
    re.IGNORECASE,
)


def _valid_payload() -> dict:
    return {
        "exhibits": [
            {
                "exhibit_number": "E-001",
                "attachment_number": "A-001",
                "title": "Signed contract excerpt",
                "source_anchor": "source:upload-001",
                "page_anchor": "pages 1-3",
                "proof_purpose": "Proves contract formation and delivery obligation.",
                "authenticity_review": {"status": "passed", "reviewer": "reviewer-001"},
                "relevance_review": {"status": "passed", "reviewer": "reviewer-001"},
                "legality_review": {"status": "passed", "reviewer": "reviewer-001"},
                "hash_or_checksum": "sha256:<redacted>",
                "confidentiality_level": "internal",
            },
            {
                "exhibit_number": "E-002",
                "attachment_number": "A-002",
                "title": "Payment record excerpt",
                "source_anchor": "source:upload-002",
                "page_anchor": "page 4",
                "proof_purpose": "Proves partial payment timeline.",
                "authenticity_review": "verified",
                "relevance_review": "verified",
                "legality_review": "verified",
                "confidentiality_level": "client-share",
            },
        ]
    }


def _policy(payload: dict | None = None) -> dict:
    return EvidenceExhibitPackagePolicyService().build_policy(payload)


def test_evidence_exhibit_package_policy_returns_template_sections():
    policy = _policy()

    assert policy["status"] == "template"
    assert policy["policy_id"] == "evidence-exhibit-package-policy-v1"
    assert policy["exhibit_metadata_schema"]
    assert policy["package_checks"]
    assert policy["blocking_issues"] == []
    assert policy["review_actions"]
    assert policy["export_manifest_fields"]
    assert policy["low_resource_validation_commands"]
    assert policy["privacy_notes"]


def test_missing_exhibit_number_proof_purpose_or_source_anchor_blocks_package():
    payload = {
        "exhibits": [
            {
                "attachment_number": "A-001",
                "page_anchor": "pages 1-2",
                "authenticity_review": "passed",
                "relevance_review": "passed",
                "legality_review": "passed",
            }
        ]
    }

    policy = _policy(payload)
    blocked_fields = {issue["field"] for issue in policy["blocking_issues"]}

    assert policy["status"] == "blocked"
    assert {"exhibit_number", "proof_purpose", "source_anchor"}.issubset(blocked_fields)
    assert policy["summary"]["ready_for_export"] is False
    assert any(check["status"] == "blocked" for check in policy["package_checks"])


def test_three_factor_review_fields_exist_in_schema_and_checks():
    policy = _policy(_valid_payload())
    schema_fields = {field["name"] for field in policy["exhibit_metadata_schema"]}
    check_ids = {check["id"] for check in policy["package_checks"]}
    manifest_fields = {field["name"] for field in policy["export_manifest_fields"]}

    assert policy["status"] == "ready"
    assert {
        "authenticity_review",
        "relevance_review",
        "legality_review",
    }.issubset(schema_fields)
    assert "three-factor-review-complete" in check_ids
    assert "three_factor_review_summary" in manifest_fields
    assert policy["summary"]["three_factor_review_count"] == 3


def test_missing_page_anchor_or_failed_three_factor_review_blocks_export():
    payload = _valid_payload()
    payload["exhibits"][0]["page_anchor"] = ""
    payload["exhibits"][1]["legality_review"] = "failed"

    policy = _policy(payload)
    issue_fields = {issue["field"] for issue in policy["blocking_issues"]}
    check_ids = {issue["check_id"] for issue in policy["blocking_issues"]}

    assert policy["status"] == "blocked"
    assert "page_anchor" in issue_fields
    assert "legality_review" in issue_fields
    assert "page-anchors-complete" in check_ids
    assert "three-factor-review-complete" in check_ids


def test_duplicate_exhibit_numbers_block_package():
    payload = _valid_payload()
    payload["exhibits"][1]["exhibit_number"] = "E-001"

    policy = _policy(payload)

    assert policy["status"] == "blocked"
    assert any(issue["id"] == "duplicate-exhibit-number-E-001" for issue in policy["blocking_issues"])
    assert any(action["id"] == "review-numbering-complete" for action in policy["review_actions"])


def test_policy_payload_has_no_sensitive_patterns():
    serialized = json.dumps(_policy(_valid_payload()), ensure_ascii=False)

    assert SENSITIVE_PATTERN.search(serialized) is None


def test_evidence_exhibit_package_policy_route_returns_template_and_ready_package():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/evidence-exhibit-package-policy")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "template"

    post_response = client.post("/api/v1/maintenance/evidence-exhibit-package-policy", json=_valid_payload())
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
