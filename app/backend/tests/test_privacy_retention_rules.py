import json

import pytest

from services.privacy_retention_rules import PrivacyRetentionRulesService


PRIVATE_EMAIL = "retention-client@example.test"
PRIVATE_KEY = "sk-PRIVATE_RETENTION_KEY_SHOULD_NOT_LEAK"


def test_privacy_retention_rules_evaluate_known_artifacts():
    result = PrivacyRetentionRulesService().build_policy(
        [
            {"artifact_id": "doc-001", "artifact_type": "uploaded_legal_document"},
            {"artifact_id": "quota-001", "artifact_type": "quota_usage_event"},
        ]
    )

    assert result["status"] == "ready"
    assert result["summary"]["evaluated_artifact_count"] == 2
    assert result["evaluations"][0]["retention_days"] == 90
    assert result["evaluations"][1]["requires_reviewer_confirmation"] is False
    assert result["privacy_boundary"]["raw_document_text_included"] is False


def test_privacy_retention_rules_redacts_unsafe_ids_and_unknown_types():
    result = PrivacyRetentionRulesService().build_policy(
        [
            {
                "artifact_id": PRIVATE_EMAIL,
                "artifact_type": "unknown_private_artifact",
                "raw_document_text": "PRIVATE LEGAL TEXT",
                "api_key": PRIVATE_KEY,
            }
        ]
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["summary"]["unknown_artifact_count"] == 1
    assert result["evaluations"][0]["artifact_id"] == "artifact_id_redacted"
    assert result["evaluations"][0]["reason_codes"] == ["unknown_artifact_type"]
    assert PRIVATE_EMAIL not in rendered
    assert PRIVATE_KEY not in rendered
    assert "PRIVATE LEGAL TEXT" not in rendered


def test_privacy_retention_rules_route_returns_policy_and_evaluation():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/privacy/retention-rules")
    post_response = client.post(
        "/api/v1/maintenance/privacy/retention-rules",
        json={"artifacts": [{"artifact_id": "report-001", "artifact_type": "deep_review_report"}]},
    )

    assert get_response.status_code == 200
    assert post_response.status_code == 200
    assert get_response.json()["data"]["summary"]["rule_count"] >= 5
    assert post_response.json()["data"]["evaluations"][0]["retention_class"] == "deep_review_report"
