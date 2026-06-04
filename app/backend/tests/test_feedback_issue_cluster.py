import json
import re

from services.feedback_issue_cluster import FeedbackIssueClusterService


SENSITIVE_PATTERN = re.compile(
    r"(client@example\.com|13800138000|11010519491231002X|sk-[A-Za-z0-9]{20,}|full private narrative)",
    re.IGNORECASE,
)


def test_repeated_feedback_items_merge_into_issue_cluster():
    report = FeedbackIssueClusterService().cluster(
        [
            {
                "id": "ticket-upload-1",
                "content": "PDF upload timed out during extraction for a paid lawyer.",
                "segment": "lawyer",
                "tags": ["paid"],
            },
            {
                "id": "ticket-upload-2",
                "message": "Scanned PDF upload failed and OCR extraction stayed blank.",
                "user_segment": "lawyer",
            },
            {
                "id": "ticket-export-1",
                "content": "Exported DOCX layout has broken formatting.",
                "segment": "legal_ops",
            },
        ]
    )

    upload_cluster = next(
        cluster
        for cluster in report["clusters"]
        if cluster["normalized_topic"] == "document_upload_or_extraction_failure"
    )

    assert upload_cluster["count"] == 2
    assert upload_cluster["counts"]["feedback_items"] == 2
    assert upload_cluster["severity"] in {"medium", "high"}
    assert upload_cluster["affected_user_segment_tags"] == ["lawyer", "paid_user"]
    assert upload_cluster["evidence_refs"] == ["id:ticket-upload-1", "id:ticket-upload-2"]
    assert report["summary"]["cluster_count"] == 2


def test_pii_and_long_raw_feedback_are_not_echoed():
    long_private_text = "full private narrative " + ("case detail " * 80)
    report = FeedbackIssueClusterService().cluster(
        [
            {
                "id": "client@example.com",
                "content": (
                    "User client@example.com phone 13800138000 id 11010519491231002X "
                    "reported a data leak with sk-" + ("a" * 24) + " " + long_private_text
                ),
                "segment": "client@example.com",
            }
        ]
    )
    serialized = json.dumps(report, ensure_ascii=False)
    cluster = report["clusters"][0]

    assert cluster["normalized_topic"] == "privacy_or_security_exposure"
    assert cluster["severity"] == "critical"
    assert cluster["evidence_refs"][0].startswith("hash:")
    assert report["privacy"]["raw_feedback_echoed"] is False
    assert report["privacy"]["pii_returned"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_declares_low_resource_no_model_processing():
    report = FeedbackIssueClusterService().cluster([])

    assert report["method"]["mode"] == "deterministic_local_rules"
    assert report["method"]["model_calls"] == 0
    assert report["method"]["external_network_calls"] == 0
    assert report["method"]["stores_raw_feedback"] is False
    assert report["method"]["max_input_items"] <= 250
    assert report["summary"]["raw_payload_echoed"] is False


def test_feedback_issue_cluster_route_is_callable():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).post(
        "/api/v1/maintenance/feedback/issue-clusters",
        json={"items": [{"id": "ticket-1", "content": "Cannot login after payment.", "segment": "paid"}]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["clusters"][0]["normalized_topic"] == "payment_or_access_blocker"
    assert payload["data"]["method"]["model_calls"] == 0
