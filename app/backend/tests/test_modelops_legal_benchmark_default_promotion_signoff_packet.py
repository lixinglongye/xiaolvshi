import json
import re

from services.modelops_legal_benchmark_default_promotion_signoff_packet import (
    ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def _ready_checklist(model_id: str = "gemini-2.5-flash-lite") -> dict:
    return {
        "id": "modelops-legal-benchmark-default-promotion-checklist",
        "title": "ModelOps legal benchmark default-promotion checklist",
        "status": "review_required",
        "decision": {
            "status": "review_required",
            "default_change_allowed_by_checklist": False,
            "configuration_change_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
            "maintainer_review_required": True,
        },
        "summary": {
            "source_count": 3,
            "checklist_row_count": 1,
            "ready_for_maintainer_review_count": 1,
            "review_required_count": 0,
            "blocked_count": 0,
            "raw_input_field_count": 0,
            "configuration_written": False,
            "env_file_written": False,
            "approval_record_written": False,
            "gateway_called": False,
            "network_called": False,
            "raw_payload_echoed": False,
            "raw_model_output_returned": False,
        },
        "checklist_rows": [
            {
                "id": "legal-benchmark-default-promotion-checklist-1",
                "requirement_id": "legal-fixture-promotion-contract-review",
                "fixture_id": "contract-risk-review-basic",
                "task": "legal_review",
                "proposed_default_model": model_id,
                "model_cost_tier": "lowest",
                "checklist_status": "ready_for_maintainer_review",
                "required_signoffs": [
                    "model_ops_maintainer",
                    "legal_quality_owner",
                    "release_owner",
                ],
                "reason_codes": ["legal-fixture-evidence-ready"],
            }
        ],
        "source_status_rows": [],
        "checks": [],
        "blocking_check_ids": [],
        "warning_check_ids": ["external-signoff-required"],
    }


def test_default_promotion_signoff_packet_packages_ready_checklist_rows_without_approval_claims():
    packet = ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService().build_packet(
        {"legal_benchmark_default_promotion_checklist": _ready_checklist()}
    )
    item = packet["signoff_items"][0]
    checks = {check["id"]: check for check in packet["checks"]}

    assert packet["id"] == "modelops-legal-benchmark-default-promotion-signoff-packet"
    assert packet["status"] == "review_required"
    assert packet["summary"]["signoff_item_count"] == 1
    assert packet["summary"]["ready_for_signoff_count"] == 1
    assert packet["summary"]["recorded_signoff_count"] == 0
    assert packet["signoff_policy"]["signoff_record_written"] is False
    assert packet["signoff_policy"]["approver_identity_collected"] is False
    assert packet["decision"]["default_change_allowed_by_signoff_packet"] is False
    assert item["signoff_status"] == "ready_for_signoff"
    assert item["signoff_record_written"] is False
    assert item["approver_identity_collected"] is False
    assert item["configuration_change_allowed"] is False
    assert item["gateway_call_allowed"] is False
    assert item["traffic_shift_allowed"] is False
    assert "confirm-legal-quality-owner-review" in item["pre_signoff_checks"]
    assert checks["default-promotion-checklist-attached-not-blocked"]["status"] == "warn"
    assert checks["signoff-items-generated"]["status"] == "pass"
    assert checks["no-signoff-record-written"]["status"] == "pass"


def test_default_promotion_signoff_packet_blocks_when_checklist_blocks():
    checklist = _ready_checklist()
    checklist["status"] = "blocked"
    checklist["blocking_check_ids"] = ["default-promotion-bridge-attached-not-blocked"]
    checklist["summary"]["blocked_count"] = 1
    checklist["checklist_rows"][0]["checklist_status"] = "blocked"

    packet = ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService().build_packet(
        {"legal_benchmark_default_promotion_checklist": checklist}
    )

    assert packet["status"] == "blocked"
    assert "default-promotion-checklist-attached-not-blocked" in packet["blocking_check_ids"]
    assert packet["signoff_items"][0]["signoff_status"] == "blocked"
    assert packet["decision"]["signoff_release_action"] == "block_default_promotion"
    assert "checklist-blocked" in packet["signoff_items"][0]["reason_codes"]


def test_default_promotion_signoff_packet_missing_checklist_builds_review_packet():
    packet = ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService().build_packet({})

    assert packet["status"] == "review_required"
    assert packet["summary"]["checklist_status"] == "review_required"
    assert packet["summary"]["signoff_item_count"] >= 0
    assert packet["privacy_boundary"]["metadata_only"] is True
    assert packet["claim_boundary"]["maintainer_approval_claimed"] is False


def test_default_promotion_signoff_packet_redacts_sensitive_values():
    checklist = _ready_checklist("sk-" + ("e" * 24))
    payload = {
        "legal_benchmark_default_promotion_checklist": checklist,
        "api_key": "sk-" + ("f" * 24),
        "raw_output": "RAW_PRIVATE_SIGNOFF_SHOULD_NOT_LEAK",
    }

    packet = ModelOpsLegalBenchmarkDefaultPromotionSignoffPacketService().build_packet(payload)
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["summary"]["raw_input_field_count"] >= 2
    assert packet["summary"]["configuration_written"] is False
    assert packet["summary"]["network_called"] is False
    assert packet["claim_boundary"]["signoff_record_claimed"] is False
    assert "redacted-sensitive-value" in serialized
    assert "RAW_PRIVATE_SIGNOFF_SHOULD_NOT_LEAK" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_default_promotion_signoff_packet_aihub_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()["data"]
    assert direct_payload["id"] == "modelops-legal-benchmark-default-promotion-signoff-packet"
    assert direct_payload["summary"]["network_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/legal-benchmark-default-promotion-signoff-packet",
        json={
            "legal_benchmark_default_promotion_checklist": {
                "status": "blocked",
                "summary": {"blocked_count": 1, "checklist_row_count": 0},
                "blocking_check_ids": ["synthetic-checklist-block"],
                "checklist_rows": [],
            }
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["legal_benchmark_default_promotion_signoff_packet"]["id"]
        == "modelops-legal-benchmark-default-promotion-signoff-packet"
    )
    assert any(
        check["source_key"] == "legal_benchmark_default_promotion_signoff_packet"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
