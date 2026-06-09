import json
import re

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.user_need_legal_document_benchmark_evidence import (
    UserNeedLegalDocumentBenchmarkEvidenceService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b",
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


def _passing_payload() -> dict:
    document_outputs = _passing_document_outputs()
    fact_outputs = _passing_fact_consistency_outputs()
    return {
        "document_benchmark_outputs": document_outputs,
        "document_fact_consistency_outputs": fact_outputs,
        "cheap_first_gate": {
            "observations": _passing_observations(),
            "document_benchmark_outputs": document_outputs,
            "document_fact_consistency_outputs": fact_outputs,
            "run_metadata": {
                "fixture-service-agreement-small": {
                    "phase": "cheap_first",
                    "model": "gemini-2.5-flash-lite",
                    "estimated_cost_usd": 0.00009,
                }
            },
        },
    }


def test_user_need_legal_document_benchmark_evidence_defaults_to_not_run_gaps():
    bridge = UserNeedLegalDocumentBenchmarkEvidenceService().build_bridge()

    assert bridge["status"] == "ready_with_blockers"
    assert bridge["summary"]["need_count"] >= 6
    assert bridge["summary"]["high_priority_blocked_need_count"] == 0
    assert bridge["summary"]["not_run_need_count"] >= bridge["summary"]["high_priority_need_count"]
    assert bridge["summary"]["document_evaluation_status"] == "not_run"
    assert bridge["summary"]["fact_consistency_status"] == "not_run"
    assert bridge["summary"]["local_rule_baseline_status"] == "pass"
    assert bridge["summary"]["cheap_first_gate_status"] == "not_run"
    assert bridge["summary"]["cheap_first_default_change_allowed"] is False
    rows = {row["need_id"]: row for row in bridge["evidence_rows"]}
    assert rows["traceable-legal-review"]["evidence_status"] == "not_run"
    assert "ldoc-civil-complaint-mini" in rows["traceable-legal-review"]["document_case_ids"]
    assert rows["traceable-legal-review"]["fact_consistency_case_ids"]
    assert "document-benchmark-not-run" in rows["traceable-legal-review"]["reason_codes"]
    assert rows["feedback-to-roadmap-loop"]["evidence_status"] == "blocked"
    assert "no-linked-legal-document-benchmark-case" in rows["feedback-to-roadmap-loop"]["reason_codes"]


def test_user_need_legal_document_benchmark_evidence_accepts_passing_local_payload():
    bridge = UserNeedLegalDocumentBenchmarkEvidenceService().build_bridge(_passing_payload())

    assert bridge["status"] == "ready_with_blockers"
    assert bridge["summary"]["document_evaluation_status"] == "pass"
    assert bridge["summary"]["document_evaluation_score"] == 100
    assert bridge["summary"]["fact_consistency_status"] == "pass"
    assert bridge["summary"]["fact_consistency_score"] == 100
    assert bridge["summary"]["cheap_first_gate_status"] == "ready"
    assert bridge["summary"]["cheap_first_default_change_allowed"] is True
    rows = {row["need_id"]: row for row in bridge["evidence_rows"]}
    assert rows["traceable-legal-review"]["evidence_status"] == "ready"
    assert "user-need-document-evidence-ready" in rows["traceable-legal-review"]["reason_codes"]
    assert rows["cheap-first-review-routing"]["cheap_first_default_change_allowed"] is True
    assert rows["feedback-to-roadmap-loop"]["evidence_status"] == "blocked"
    assert bridge["ready_need_ids"]
    assert bridge["blocked_need_ids"] == ["feedback-to-roadmap-loop"]


def test_user_need_legal_document_benchmark_evidence_is_metadata_only():
    payload = _passing_payload()
    payload["document_benchmark_outputs"]["ldoc-civil-complaint-mini"]["generated_text"] = (
        "raw candidate should not echo; contact test@example.com; TOKEN_SHOULD_NOT_APPEAR_1234567890"
    )
    bridge = UserNeedLegalDocumentBenchmarkEvidenceService().build_bridge(payload)
    serialized = json.dumps(bridge, ensure_ascii=False)

    assert bridge["privacy_boundary"]["metadata_only"] is True
    assert bridge["privacy_boundary"]["returns_document_snippets"] is False
    assert bridge["privacy_boundary"]["returns_raw_candidate_text"] is False
    assert bridge["privacy_boundary"]["returns_payload_bodies"] is False
    assert bridge["privacy_boundary"]["returns_credentials"] is False
    assert bridge["claim_boundary"]["public_benchmark_score_claimed"] is False
    assert bridge["claim_boundary"]["default_model_changed"] is False
    assert "raw candidate should not echo" not in serialized
    assert "test@example.com" not in serialized
    assert "TOKEN_SHOULD_NOT_APPEAR_1234567890" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_user_need_legal_document_benchmark_evidence_route_returns_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/maintenance/user-needs/legal-document-benchmark-evidence")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["local_rule_baseline_status"] == "pass"

    post_response = client.post(
        "/api/v1/maintenance/user-needs/legal-document-benchmark-evidence",
        json=_passing_payload(),
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["success"] is True
    assert post_payload["data"]["summary"]["document_evaluation_status"] == "pass"
