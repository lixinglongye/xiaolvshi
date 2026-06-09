import json
import re

from services.feedback_user_need_legal_document_benchmark_backlog import (
    FeedbackUserNeedLegalDocumentBenchmarkBacklogService,
)


SENSITIVE_PATTERN = re.compile(
    r"(client@example\.com|13800138000|TOKEN_SHOULD_NOT_APPEAR|private narrative|raw feedback body)",
    re.IGNORECASE,
)


def test_feedback_user_need_legal_document_benchmark_backlog_builds_ranked_rows():
    backlog = FeedbackUserNeedLegalDocumentBenchmarkBacklogService().build_backlog()

    assert backlog["status"] in {"ready_with_backlog", "blocked", "ready"}
    assert backlog["method"]["type"] == "feedback-user-need-legal-document-benchmark-backlog"
    assert backlog["summary"]["cluster_count"] >= 3
    assert backlog["summary"]["model_calls"] == "not_required"
    assert backlog["summary"]["network_access"] == "disabled"
    assert backlog["privacy_boundary"]["metadata_only"] is True
    assert backlog["privacy_boundary"]["returns_raw_feedback"] is False
    assert backlog["privacy_boundary"]["returns_user_feedback_text"] is False
    assert backlog["claim_boundary"]["feedback_resolution_claimed"] is False

    legal_quality_row = next(
        row for row in backlog["backlog_rows"] if row["normalized_topic"] == "legal_output_quality_risk"
    )
    assert legal_quality_row["primary_need_id"] == "traceable-legal-review"
    assert "traceable-legal-review" in legal_quality_row["mapped_need_ids"]
    assert legal_quality_row["severity"] == "high"
    assert legal_quality_row["benchmark_action_status"] in {"blocked", "create_fixture", "review_required", "ready"}
    assert legal_quality_row["priority_score"] >= 50
    assert "feedback-user-need-legal-document-benchmark-backlog" in legal_quality_row["release_gate_links"]
    assert legal_quality_row["suggested_fixture_ids"]
    assert any(code.startswith("feedback-topic-legal_output_quality_risk") for code in legal_quality_row["reason_codes"])


def test_feedback_user_need_legal_document_benchmark_backlog_maps_custom_clusters_to_needs():
    backlog = FeedbackUserNeedLegalDocumentBenchmarkBacklogService().build_backlog(
        {
            "items": [
                {
                    "id": "ticket-legal-citation-1",
                    "category": "bug",
                    "content": "Wrong law and hallucination in generated legal report.",
                    "segment": "lawyer",
                    "severity": "high",
                },
                {
                    "id": "ticket-upload-1",
                    "category": "bug",
                    "content": "Scanned PDF upload failed and OCR output stayed blank.",
                    "segment": "paid lawyer",
                    "severity": "medium",
                },
                {
                    "id": "ticket-ui-1",
                    "category": "suggestion",
                    "content": "Need a clearer summary and next step after review.",
                    "segment": "legal_ops",
                },
            ]
        }
    )

    topics = {row["normalized_topic"]: row for row in backlog["backlog_rows"]}
    assert topics["legal_output_quality_risk"]["primary_need_id"] == "traceable-legal-review"
    assert topics["document_upload_or_extraction_failure"]["primary_need_id"] == "robust-extraction-quality"
    assert topics["feature_or_usability_request"]["primary_need_id"] == "plain-language-actionability"
    assert topics["document_upload_or_extraction_failure"]["safe_evidence_ref_count"] == 1
    assert backlog["summary"]["mapped_need_count"] >= 3
    assert backlog["summary"]["document_type_suggestion_count"] >= 1


def test_feedback_user_need_legal_document_benchmark_backlog_is_metadata_only():
    backlog = FeedbackUserNeedLegalDocumentBenchmarkBacklogService().build_backlog(
        {
            "items": [
                {
                    "id": "client@example.com",
                    "content": (
                        "raw feedback body private narrative client@example.com 13800138000 "
                        "TOKEN_SHOULD_NOT_APPEAR reported a data leak in a legal document upload"
                    ),
                    "segment": "client@example.com",
                }
            ]
        }
    )
    serialized = json.dumps(backlog, ensure_ascii=False)
    row = backlog["backlog_rows"][0]

    assert row["normalized_topic"] == "privacy_or_security_exposure"
    assert row["primary_need_id"] == "privacy-safe-upload"
    assert row["safe_evidence_ref_count"] == 1
    assert backlog["privacy_boundary"]["returns_pii"] is False
    assert backlog["privacy_boundary"]["returns_payload_bodies"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_feedback_user_need_legal_document_benchmark_backlog_route_returns_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/feedback/user-need-legal-document-benchmark-backlog")
    assert get_response.status_code == 200
    assert get_response.json()["success"] is True
    assert get_response.json()["data"]["method"]["type"] == "feedback-user-need-legal-document-benchmark-backlog"

    post_response = client.post(
        "/api/v1/maintenance/feedback/user-need-legal-document-benchmark-backlog",
        json={"items": [{"id": "ticket-1", "content": "Wrong law citation in report.", "severity": "high"}]},
    )
    assert post_response.status_code == 200
    payload = post_response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["cluster_count"] == 1
    assert payload["data"]["backlog_rows"][0]["primary_need_id"] == "traceable-legal-review"
