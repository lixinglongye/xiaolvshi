import json
import re

from services.feedback_user_need_legal_document_benchmark_release_packet import (
    FeedbackUserNeedLegalDocumentBenchmarkReleasePacketService,
)
from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService
from services.legal_review_benchmark import LegalReviewBenchmarkService


SENSITIVE_PATTERN = re.compile(
    r"(client@example\.com|13800138000|TOKEN_SHOULD_NOT_APPEAR|private narrative|raw feedback body)",
    re.IGNORECASE,
)


def _passing_observations() -> dict[str, dict]:
    template = LegalReviewBenchmarkService().build_fixture_smoke_template()
    return {
        fixture["id"]: {
            "route": fixture["expected_routes"][0],
            "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
        }
        for fixture in template["fixtures"]
    }


def _passing_document_outputs() -> dict[str, dict]:
    suite = LegalDocumentBenchmarkSuiteService().build_suite()
    return {
        case["id"]: {
            "sections": {section: "present" for section in case["required_sections"]},
            "citations": case["expected_citations"],
            "risk_labels": case["expected_risk_labels"],
            "pii_findings": [],
        }
        for case in suite["benchmark_cases"]
    }


def _passing_fact_consistency_outputs() -> dict[str, dict]:
    suite = LegalDocumentFactConsistencyBenchmarkService().build_suite()
    return {
        case["id"]: {
            "amounts": {item["id"]: item["value"] for item in case["amount_expectations"]},
            "deadlines": {item["id"]: item["value"] for item in case["deadline_expectations"]},
            "facts": list(case["required_fact_ids"]),
        }
        for case in suite["benchmark_cases"]
    }


def _passing_legal_document_evidence() -> dict:
    document_outputs = _passing_document_outputs()
    fact_outputs = _passing_fact_consistency_outputs()
    return {
        "document_benchmark_outputs": document_outputs,
        "document_fact_consistency_outputs": fact_outputs,
        "cheap_first_gate": {
            "observations": _passing_observations(),
            "document_benchmark_outputs": document_outputs,
            "document_fact_consistency_outputs": fact_outputs,
        },
    }


def test_feedback_release_packet_defaults_to_review_or_block_without_claiming_resolution():
    packet = FeedbackUserNeedLegalDocumentBenchmarkReleasePacketService().build_packet()

    assert packet["status"] in {"blocked", "review_required"}
    assert packet["method"]["type"] == "feedback-user-need-legal-document-benchmark-release-packet"
    assert packet["summary"]["release_row_count"] >= 3
    assert packet["summary"]["customer_resolution_claimed"] is False
    assert packet["summary"]["model_calls"] == "not_required"
    assert packet["summary"]["network_access"] == "disabled"
    assert packet["privacy_boundary"]["metadata_only"] is True
    assert packet["privacy_boundary"]["returns_raw_feedback"] is False
    assert packet["privacy_boundary"]["returns_customer_notes"] is False
    assert packet["claim_boundary"]["feedback_resolution_claimed"] is False

    assert any(row["release_action_status"] in {"blocked", "release_review_required"} for row in packet["release_rows"])
    assert all(row["customer_resolution_claimed"] is False for row in packet["release_rows"])


def test_feedback_release_packet_allows_customer_resolution_only_after_release_observation_passes():
    packet = FeedbackUserNeedLegalDocumentBenchmarkReleasePacketService().build_packet(
        {
            "items": [
                {
                    "id": "ticket-export-1",
                    "content": "Export format issue in client delivery.",
                    "severity": "low",
                }
            ],
            "legal_document_evidence": _passing_legal_document_evidence(),
            "release_observations": [
                {
                    "cluster_id": "feedback-export_or_delivery_format_issue",
                    "normalized_topic": "export_or_delivery_format_issue",
                    "current_state": "release_validation",
                    "release_validation_status": "pass",
                    "implementation_review_status": "pass",
                    "customer_resolution_note": "Export readiness gate is fixed for reviewed formats.",
                    "release_gate_links": [
                        "feedback-user-need-legal-document-benchmark-release-packet",
                        "legal-document-export-readiness",
                    ],
                }
            ],
        }
    )

    assert packet["status"] == "ready"
    assert packet["summary"]["customer_resolution_ready_count"] == 1
    row = packet["release_rows"][0]
    assert row["normalized_topic"] == "export_or_delivery_format_issue"
    assert row["primary_need_id"] == "plain-language-actionability"
    assert row["benchmark_action_status"] == "ready"
    assert row["legal_document_evidence_status"] == "ready"
    assert row["release_action_status"] == "customer_resolution_ready"
    assert row["customer_resolution_allowed"] is True
    assert row["customer_resolution_claimed"] is False
    assert "customer_visible_resolution" in row["lifecycle_next_allowed_states"]


def test_feedback_release_packet_keeps_high_risk_fixture_gap_in_review():
    packet = FeedbackUserNeedLegalDocumentBenchmarkReleasePacketService().build_packet(
        {
            "items": [
                {
                    "id": "ticket-legal-quality-1",
                    "content": "Wrong law and hallucination in generated legal report.",
                    "severity": "high",
                }
            ],
            "legal_document_evidence": _passing_legal_document_evidence(),
            "release_observations": [
                {
                    "cluster_id": "feedback-legal_output_quality_risk",
                    "current_state": "release_validation",
                    "release_validation_status": "pass",
                    "customer_resolution_note": "Citation and evidence checks passed for reviewed fixture coverage.",
                }
            ],
        }
    )

    row = packet["release_rows"][0]
    assert row["high_risk"] is True
    assert row["benchmark_action_status"] == "create_fixture"
    assert row["release_action_status"] == "release_review_required"
    assert row["customer_resolution_allowed"] is False
    assert "suggested-fixture-work-present" in row["reason_codes"]


def test_feedback_release_packet_is_metadata_only_for_sensitive_inputs():
    packet = FeedbackUserNeedLegalDocumentBenchmarkReleasePacketService().build_packet(
        {
            "items": [
                {
                    "id": "client@example.com",
                    "content": (
                        "raw feedback body private narrative client@example.com 13800138000 "
                        "TOKEN_SHOULD_NOT_APPEAR reported export issue"
                    ),
                    "segment": "client@example.com",
                }
            ],
            "release_observations": [
                {
                    "cluster_id": "feedback-export_or_delivery_format_issue",
                    "customer_resolution_note": (
                        "private narrative client@example.com TOKEN_SHOULD_NOT_APPEAR should not echo"
                    ),
                }
            ],
        }
    )
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["privacy_boundary"]["returns_raw_feedback_text"] is False
    assert packet["privacy_boundary"]["returns_public_resolution_text"] is False
    assert packet["privacy_boundary"]["returns_payload_bodies"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_feedback_release_packet_route_returns_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/feedback/user-need-legal-document-benchmark-release-packet")
    assert get_response.status_code == 200
    assert get_response.json()["success"] is True
    assert (
        get_response.json()["data"]["method"]["type"]
        == "feedback-user-need-legal-document-benchmark-release-packet"
    )

    post_response = client.post(
        "/api/v1/maintenance/feedback/user-need-legal-document-benchmark-release-packet",
        json={
            "items": [{"id": "ticket-1", "content": "Export format issue in client delivery.", "severity": "low"}],
            "legal_document_evidence": _passing_legal_document_evidence(),
            "release_observations": [
                {
                    "cluster_id": "feedback-export_or_delivery_format_issue",
                    "normalized_topic": "export_or_delivery_format_issue",
                    "release_validation_status": "pass",
                    "implementation_review_status": "pass",
                    "customer_resolution_note": "Export gate passed for reviewed formats.",
                }
            ],
        },
    )
    assert post_response.status_code == 200
    payload = post_response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["release_row_count"] == 1
    assert payload["data"]["release_rows"][0]["release_action_status"] == "customer_resolution_ready"
