import json
import re

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import (
    LegalDocumentFactConsistencyBenchmarkService,
)
from services.small_legal_document_benchmark_runbook_evidence import (
    SmallLegalDocumentBenchmarkRunbookEvidenceService,
)


SECRET_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def _document_outputs() -> dict:
    suite = LegalDocumentBenchmarkSuiteService().build_suite()
    return {
        case["id"]: {
            "sections": {section: "present" for section in case["required_sections"]},
            "citations": case["expected_citations"],
            "risk_labels": case["expected_risk_labels"],
            "pii_findings": [],
            "generated_text": "Synthetic redacted output only.",
        }
        for case in suite["benchmark_cases"]
    }


def _fact_outputs() -> dict:
    suite = LegalDocumentFactConsistencyBenchmarkService().build_suite()
    outputs: dict[str, dict] = {}
    for case in suite["benchmark_cases"]:
        outputs[case["id"]] = {
            "amounts": {item["id"]: item["value"] for item in case["amount_expectations"]},
            "deadlines": {item["id"]: item["value"] for item in case["deadline_expectations"]},
            "facts": list(case["required_fact_ids"]),
        }
    return outputs


def _final_delivery_payload() -> dict:
    return {
        "action": "deliver_to_client",
        "delivery_package": {
            "package": {
                "package_id": "package-001",
                "case_id": "case-001",
                "current_version_id": "version-002",
                "delivery_channel": "client_portal",
            },
            "documents": [
                {
                    "document_id": "doc-001",
                    "document_type": "complaint",
                    "version_id": "version-002",
                    "export_formats": ["pdf", "docx"],
                }
            ],
            "source_support": {
                "status": "complete",
                "citation_count": 4,
                "unsupported_claim_count": 0,
                "evidence_links": ["evidence-001", "evidence-002"],
            },
            "missing_facts": {"status": "resolved", "items": []},
            "lawyer_review": {
                "status": "approved",
                "reviewer_id": "lawyer-001",
                "reviewed_at": "2026-06-04T08:00:00Z",
                "reviewed_version_id": "version-002",
            },
            "client_transparency": {
                "notice_present": True,
                "client_visible": True,
                "risk_notice_included": True,
                "scope_limits_included": True,
            },
            "export": {"formats": ["pdf", "docx"], "final_format": "pdf", "version_locked": True},
            "version_notes": {
                "current_version_id": "version-002",
                "previous_version_id": "version-001",
                "summary_present": True,
                "generated_at": "2026-06-04T08:05:00Z",
            },
        },
        "version_diff": {
            "version_id": "version-002",
            "previous_version_id": "version-001",
            "change_summary": "Clarified payment deadline and source support.",
            "changed_sections": ["payment", "evidence"],
            "reviewer_role": "lawyer",
            "client_visible_summary": "Payment deadline language was clarified.",
            "risk_change_summary": "No risk level change.",
            "source_support_status": "complete",
        },
        "export_readiness": {
            "required_fields_complete": True,
            "blockers_cleared": True,
            "lawyer_review_status": "approved",
            "source_support_complete": True,
            "privacy_redaction_status": "pass",
            "version_locked": True,
            "export_format": "pdf",
        },
        "quota_summary": {
            "decision_status": "ready",
            "can_create_report": True,
            "reports_remaining": 3,
            "report_quota_monthly": 20,
            "quota_window": "2026-06",
        },
    }


def _passing_payload() -> dict:
    return {
        "document_benchmark_outputs": _document_outputs(),
        "document_fact_consistency_outputs": _fact_outputs(),
        "final_delivery_payload": _final_delivery_payload(),
    }


def test_small_document_runbook_default_is_review_required_template():
    packet = SmallLegalDocumentBenchmarkRunbookEvidenceService().build_evidence()

    assert packet["id"] == "small-legal-document-benchmark-runbook-evidence"
    assert packet["status"] == "review_required"
    assert packet["summary"]["document_not_run_case_count"] == packet["summary"]["document_case_count"]
    assert packet["summary"]["fact_not_run_case_count"] == packet["summary"]["fact_case_count"]
    assert packet["summary"]["delivery_ready_component_count"] == 0
    assert packet["summary"]["max_parallel_requests"] == 1
    assert packet["summary"]["model_calls"] == "not_required"
    assert packet["summary"]["network_access"] == "disabled"
    assert "document-benchmark-run" in packet["warning_check_ids"]
    assert "fact-consistency-run" in packet["warning_check_ids"]
    assert "final-delivery-gate-run" in packet["warning_check_ids"]
    assert len(packet["runbook_steps"]) == 5
    assert len(packet["document_benchmark_rows"]) == 7
    assert len(packet["fact_consistency_rows"]) == 4
    assert len(packet["delivery_gate_rows"]) == 4


def test_small_document_runbook_accepts_passing_local_results():
    packet = SmallLegalDocumentBenchmarkRunbookEvidenceService().build_evidence(_passing_payload())

    assert packet["status"] == "ready"
    assert packet["summary"]["document_passed_case_count"] == packet["summary"]["document_case_count"]
    assert packet["summary"]["fact_passed_case_count"] == packet["summary"]["fact_case_count"]
    assert packet["summary"]["delivery_ready_component_count"] == packet["summary"]["delivery_component_count"]
    assert packet["summary"]["blocked_evidence_row_count"] == 0
    assert packet["blocking_check_ids"] == []
    assert packet["warning_check_ids"] == []
    assert packet["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert packet["claim_boundary"]["production_legal_quality_claimed"] is False
    assert packet["claim_boundary"]["client_delivery_sent"] is False
    assert packet["privacy_boundary"]["metadata_only"] is True
    assert packet["privacy_boundary"]["returns_document_snippets"] is False
    assert packet["privacy_boundary"]["returns_generated_text"] is False
    assert packet["privacy_boundary"]["model_calls"] is False
    assert packet["privacy_boundary"]["network_called"] is False


def test_small_document_runbook_blocks_failed_fact_or_delivery_gate_without_echoing_raw_values():
    payload = _passing_payload()
    payload["document_fact_consistency_outputs"]["fact-lease-arrears-mini"]["amounts"]["arrears_total"] = 9000
    payload["final_delivery_payload"]["delivery_package"]["documents"][0]["raw_document_text"] = (
        "RAW_DOCUMENT_SHOULD_NOT_LEAK"
    )
    payload["final_delivery_payload"]["version_diff"]["change_summary"] = "secret sk-" + ("a" * 24)
    payload["final_delivery_payload"]["export_readiness"]["export_format"] = "exe"
    payload["document_benchmark_outputs"]["ldoc-civil-complaint-mini"]["generated_text"] = (
        "contact 13812345678"
    )

    packet = SmallLegalDocumentBenchmarkRunbookEvidenceService().build_evidence(payload)
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["status"] == "blocked"
    assert "document-benchmark-run" in packet["blocking_check_ids"]
    assert "fact-consistency-run" in packet["blocking_check_ids"]
    assert "final-delivery-gate-run" in packet["blocking_check_ids"]
    assert packet["summary"]["raw_input_field_count"] >= 3
    assert "RAW_DOCUMENT_SHOULD_NOT_LEAK" not in serialized
    assert "13812345678" not in serialized
    assert "sk-" + ("a" * 24) not in serialized
    assert not SECRET_PATTERN.search(serialized)


def test_small_document_runbook_source_links_and_validation_are_reviewable():
    packet = SmallLegalDocumentBenchmarkRunbookEvidenceService().build_evidence()

    assert packet["source_endpoints"]["runbook_evidence"].endswith("/small-document-runbook-evidence")
    assert packet["source_endpoints"]["document_benchmark"].endswith("/document-fixtures")
    assert packet["source_endpoints"]["fact_consistency"].endswith("/document-fact-consistency")
    assert packet["source_endpoints"]["final_delivery_gate"].endswith("/final-document-delivery-release-gate")
    assert "tests/test_small_legal_document_benchmark_runbook_evidence.py" in packet["validation_commands"][0]
    assert all(step["model_call"] is False for step in packet["runbook_steps"])
    assert all(step["network_call"] is False for step in packet["runbook_steps"])
    assert any(row["source"] == "legal_document_benchmark_suite" for row in packet["evidence_rows"])
    assert any(row["source"] == "legal_document_fact_consistency_benchmark" for row in packet["evidence_rows"])
    assert any(row["source"] == "final_document_delivery_release_gate" for row in packet["evidence_rows"])


def test_small_document_runbook_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "review_required"

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence",
        json=_passing_payload(),
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
