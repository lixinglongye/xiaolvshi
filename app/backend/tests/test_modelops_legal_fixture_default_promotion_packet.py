import json
import re

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.modelops_legal_fixture_default_promotion_packet import (
    ModelOpsLegalFixtureDefaultPromotionPacketService,
)
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
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
            "amounts": {
                item["id"]: item["value"]
                for item in case["amount_expectations"]
            },
            "deadlines": {
                item["id"]: item["value"]
                for item in case["deadline_expectations"]
            },
            "facts": list(case["required_fact_ids"]),
        }
        for case in suite["benchmark_cases"]
    }


def test_legal_fixture_default_promotion_packet_is_not_ready_by_default():
    packet = ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet()
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["status"] == "not_ready"
    assert packet["decision"]["configuration_change_allowed"] is False
    assert packet["decision"]["gateway_call_allowed"] is False
    assert packet["summary"]["source_gate_status"] == "not_run"
    assert packet["summary"]["source_default_change_evidence_allowed"] is False
    assert packet["summary"]["document_benchmark_status"] == "not_run"
    assert packet["summary"]["fact_consistency_status"] == "not_run"
    assert packet["summary"]["calibration_status"] == "pass"
    assert packet["summary"]["linked_calibration_task_count"] == 4
    assert packet["summary"]["configuration_written"] is False
    assert packet["summary"]["gateway_called"] is False
    assert packet["summary"]["traffic_shifted"] is False
    assert packet["summary"]["raw_text_returned"] is False
    assert packet["privacy_boundary"]["returns_raw_fixture_text"] is False
    assert packet["privacy_boundary"]["returns_calibration_payloads"] is False
    assert packet["privacy_boundary"]["returns_document_snippets"] is False
    assert packet["claim_boundary"]["automatic_default_change_claimed"] is False
    assert packet["claim_boundary"]["fact_consistency_benchmark_scores_claimed"] is False
    assert packet["claim_boundary"]["maintainer_approval_claimed"] is False
    assert all(item["promotion_status"] == "not_ready" for item in packet["promotion_items"])
    assert "generated_text" not in serialized
    assert "output_text" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_legal_fixture_default_promotion_packet_ready_after_gate_and_document_benchmark_pass():
    packet = ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        }
    )

    assert packet["status"] == "ready_for_maintainer_review"
    assert packet["summary"]["source_gate_status"] == "ready"
    assert packet["summary"]["source_default_change_evidence_allowed"] is True
    assert packet["summary"]["document_benchmark_status"] == "pass"
    assert packet["summary"]["fact_consistency_status"] == "pass"
    assert packet["summary"]["fact_consistency_score"] == 100
    assert packet["summary"]["fact_consistency_case_count"] == 4
    assert packet["summary"]["document_coverage_status"] == "ready"
    assert packet["summary"]["calibration_status"] == "pass"
    assert packet["summary"]["linked_calibration_task_count"] == 4
    assert packet["summary"]["calibration_blocking_count"] == 0
    assert packet["summary"]["calibration_warning_count"] == 0
    assert packet["summary"]["ready_for_review_count"] == 3
    assert packet["required_signoffs"] == ["maintainer_owner", "model_ops_reviewer", "legal_quality_reviewer"]
    assert packet["decision"]["default_change_allowed_by_packet"] is False
    assert packet["decision"]["requires_cheap_first_calibration_pass"] is True
    assert packet["decision"]["configuration_change_allowed"] is False
    assert all(item["promotion_status"] == "ready_for_maintainer_review" for item in packet["promotion_items"])
    assert all(item["fact_consistency_status"] == "pass" for item in packet["promotion_items"])
    assert all(item["calibration_status"] == "pass" for item in packet["promotion_items"])
    assert all(item["linked_calibration_task_ids"] for item in packet["promotion_items"])
    assert all("cheap-first calibration pass" in item["required_evidence"] for item in packet["promotion_items"])
    assert all(item["configuration_change_allowed"] is False for item in packet["promotion_items"])
    assert all("maintainer signoff outside this service" in item["required_evidence"] for item in packet["promotion_items"])
    assert any(item["id"] == "fact-consistency-pass" and item["passed"] for item in packet["evidence_checklist"])
    assert any(item["id"] == "cheap-first-calibration-pass" and item["passed"] for item in packet["evidence_checklist"])
    assert packet["source_gate_links"]["cheap_first_calibration"] == "/api/v1/aihub/models/cheap-first-calibration"


def test_legal_fixture_default_promotion_packet_aihub_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-fixture-cheap-first-default-promotion-packet")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()
    assert direct_payload["success"] is True
    assert direct_payload["data"]["summary"]["calibration_status"] == "pass"
    assert direct_payload["data"]["decision"]["requires_cheap_first_calibration_pass"] is True
    assert direct_payload["data"]["privacy_boundary"]["returns_calibration_payloads"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    packet = models_payload["legal_fixture_cheap_first_default_promotion_packet"]
    assert packet["summary"]["linked_calibration_task_count"] == 4
    assert packet["decision"]["configuration_change_allowed"] is False
    assert all(item["linked_calibration_task_ids"] for item in packet["promotion_items"])
    assert not SENSITIVE_PATTERN.search(json.dumps(packet, ensure_ascii=False))


def test_legal_fixture_default_promotion_packet_blocks_document_pii_failure():
    document_outputs = _passing_document_outputs()
    target_case = LegalDocumentBenchmarkSuiteService().build_suite()["benchmark_cases"][0]
    document_outputs[target_case["id"]]["generated_text"] = "\u8054\u7cfb 13812345678"

    packet = ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": document_outputs,
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        }
    )
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["status"] == "blocked"
    assert packet["summary"]["document_benchmark_status"] == "blocked"
    assert packet["summary"]["source_default_change_evidence_allowed"] is False
    assert packet["blocked_item_ids"]
    assert all(item["promotion_status"] == "blocked" for item in packet["promotion_items"])
    assert "generated_text" not in serialized
    assert "13812345678" not in serialized


def test_legal_fixture_default_promotion_packet_blocks_failed_calibration_source_gate():
    class FailingCalibrationService:
        def build_calibration(self, payload=None):
            return {
                "status": "fail",
                "calibration_rows": [
                    {
                        "id": "legal-review-balanced",
                        "status": "fail",
                        "calibration_decision": "hold_default_change",
                        "fixture_ids": ["fixture-service-agreement-small", "fixture-lease-dispute-notice-small"],
                        "release_gate_links": ["gemini-newapi-selector-replay"],
                    },
                    {
                        "id": "ocr-assist",
                        "status": "pass",
                        "calibration_decision": "keep_cheap_first_default",
                        "fixture_ids": ["fixture-low-text-pdf-page-small"],
                        "release_gate_links": ["gemini-newapi-selector-replay"],
                    },
                ],
            }

    source_gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService(
        calibration_service=FailingCalibrationService()
    ).build_gate(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        }
    )

    packet = ModelOpsLegalFixtureDefaultPromotionPacketService().build_packet({"source_gate": source_gate})

    assert packet["status"] == "blocked"
    assert packet["summary"]["calibration_status"] == "fail"
    assert packet["summary"]["calibration_blocking_count"] == 1
    assert packet["summary"]["source_default_change_evidence_allowed"] is False
    assert any(item["id"] == "cheap-first-calibration-pass" and not item["passed"] for item in packet["evidence_checklist"])
    assert any("cheap-first-calibration-not-pass" in item["reason_codes"] for item in packet["promotion_items"])
    assert packet["blocked_item_ids"]


def test_legal_fixture_default_promotion_packet_accepts_source_gate_without_echoing_raw_payload():
    service = ModelOpsLegalFixtureDefaultPromotionPacketService()
    source_gate = service.gate_service.build_gate(
        {
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        }
    )

    packet = service.build_packet({"source_gate": source_gate, "output_text": "should not echo"})
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["status"] == "ready_for_maintainer_review"
    assert packet["summary"]["source_gate_status"] == "ready"
    assert packet["summary"]["fact_consistency_status"] == "pass"
    assert "output_text" not in serialized
    assert "should not echo" not in serialized


def test_legal_fixture_default_promotion_packet_route_returns_packet():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/default-promotion-packet")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["status"] == "not_ready"

    alias_get_response = client.get(
        "/api/v1/maintenance/legal-review-benchmark/cheap-first-default-promotion-packet"
    )
    assert alias_get_response.status_code == 200
    assert alias_get_response.json()["data"]["summary"]["configuration_written"] is False

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/default-promotion-packet",
        json={
                "observations": _passing_observations(),
                "document_benchmark_outputs": _passing_document_outputs(),
                "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
            },
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["success"] is True
    assert post_payload["data"]["status"] == "ready_for_maintainer_review"
    assert post_payload["data"]["summary"]["configuration_written"] is False

    alias_post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/cheap-first-default-promotion-packet",
        json={
            "observations": _passing_observations(),
            "document_benchmark_outputs": _passing_document_outputs(),
            "document_fact_consistency_outputs": _passing_fact_consistency_outputs(),
        },
    )
    assert alias_post_response.status_code == 200
    assert alias_post_response.json()["data"]["status"] == "ready_for_maintainer_review"
