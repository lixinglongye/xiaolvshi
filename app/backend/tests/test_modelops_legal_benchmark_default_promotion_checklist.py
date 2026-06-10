import json
import re

from services.modelops_legal_benchmark_default_promotion_checklist import (
    ModelOpsLegalBenchmarkDefaultPromotionChecklistService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def _ready_bridge(model_id: str = "gemini-2.5-flash-lite") -> dict:
    return {
        "id": "modelops-legal-benchmark-default-promotion-bridge",
        "title": "ModelOps legal benchmark default-promotion bridge",
        "status": "review_required",
        "decision": {
            "status": "review_required",
            "default_change_allowed_by_bridge": False,
            "current_cheap_first_defaults_allowed": True,
            "maintainer_review_required": True,
            "configuration_change_allowed": False,
            "gateway_call_allowed": False,
            "traffic_shift_allowed": False,
            "bridge_release_action": "maintainer_review_required",
        },
        "summary": {
            "source_count": 5,
            "promotion_row_count": 1,
            "promotion_ready_count": 1,
            "promotion_blocked_count": 0,
            "blocked_default_count": 0,
            "raw_input_field_count": 0,
            "configuration_written": False,
            "gateway_called": False,
            "network_called": False,
            "raw_payload_echoed": False,
            "raw_model_output_returned": False,
        },
        "source_rows": [],
        "promotion_rows": [
            {
                "id": "legal-fixture-promotion-contract-review",
                "fixture_id": "contract-risk-review-basic",
                "task": "legal_review",
                "matter_type": "contract",
                "proposed_default_model": model_id,
                "model_cost_tier": "lowest",
                "promotion_status": "ready_for_maintainer_review",
                "bridge_status": "ready_for_maintainer_review",
                "gate_status": "ready",
                "document_benchmark_status": "ready",
                "fact_consistency_status": "ready",
                "calibration_status": "ready",
                "official_lifecycle": "stable",
                "reason_codes": ["legal-fixture-evidence-ready"],
            }
        ],
        "checks": [{"id": "gemini-lifecycle-defaults-not-blocked", "status": "pass"}],
        "blocking_check_ids": [],
        "warning_check_ids": ["maintainer-review-required"],
    }


def _signals() -> dict:
    return {
        "legal_benchmark_default_promotion_bridge": _ready_bridge(),
        "cheap_first_release_decision": {
            "status": "pass",
            "summary": {
                "default_promotion_blocked": False,
                "maintainer_review_required": False,
                "blocking_signal_count": 0,
            },
            "blocking_check_ids": [],
            "warning_check_ids": [],
        },
        "default_change_queue": {
            "status": "review_required",
            "summary": {
                "queue_item_count": 1,
                "blocked_change_count": 0,
                "review_required_count": 1,
                "configuration_written": False,
                "gateway_called": False,
            },
            "queue_items": [
                {
                    "id": "default-change-legal_review",
                    "task": "legal_review",
                    "recommended_model": "gemini-2.5-flash-lite",
                    "queue_status": "review_required",
                }
            ],
            "blocking_item_ids": [],
            "review_item_ids": ["default-change-legal_review"],
        },
    }


def test_default_promotion_checklist_joins_bridge_release_and_queue_for_review():
    checklist = ModelOpsLegalBenchmarkDefaultPromotionChecklistService().build_checklist(_signals())
    row = checklist["checklist_rows"][0]
    checks = {check["id"]: check for check in checklist["checks"]}

    assert checklist["id"] == "modelops-legal-benchmark-default-promotion-checklist"
    assert checklist["status"] == "review_required"
    assert checklist["summary"]["checklist_row_count"] == 1
    assert checklist["summary"]["review_required_count"] == 1
    assert checklist["summary"]["blocked_count"] == 0
    assert checklist["summary"]["bridge_status"] == "review_required"
    assert checklist["summary"]["release_decision_status"] == "pass"
    assert checklist["summary"]["default_change_queue_status"] == "review_required"
    assert checklist["decision"]["default_change_allowed_by_checklist"] is False
    assert checklist["decision"]["configuration_change_allowed"] is False
    assert checklist["decision"]["gateway_call_allowed"] is False
    assert checklist["decision"]["traffic_shift_allowed"] is False
    assert row["checklist_status"] == "review_required"
    assert row["matched_queue_item_id"] == "default-change-legal_review"
    assert row["default_change_allowed_by_checklist"] is False
    assert "default-change-queue-review-required" in row["reason_codes"]
    assert checks["default-promotion-bridge-attached-not-blocked"]["status"] == "warn"
    assert checks["cheap-first-release-decision-not-failed"]["status"] == "pass"
    assert checks["default-change-queue-not-blocked"]["status"] == "warn"


def test_default_promotion_checklist_blocks_when_bridge_blocks():
    signals = _signals()
    bridge = _ready_bridge()
    bridge["status"] = "blocked"
    bridge["blocking_check_ids"] = ["gemini-lifecycle-defaults-not-blocked"]
    bridge["promotion_rows"][0]["bridge_status"] = "blocked"
    signals["legal_benchmark_default_promotion_bridge"] = bridge

    checklist = ModelOpsLegalBenchmarkDefaultPromotionChecklistService().build_checklist(signals)

    assert checklist["status"] == "blocked"
    assert "default-promotion-bridge-attached-not-blocked" in checklist["blocking_check_ids"]
    assert checklist["checklist_rows"][0]["checklist_status"] == "blocked"
    assert checklist["decision"]["checklist_release_action"] == "block_default_promotion"


def test_default_promotion_checklist_blocks_when_release_decision_or_queue_blocks():
    signals = _signals()
    signals["cheap_first_release_decision"]["status"] = "fail"
    signals["cheap_first_release_decision"]["blocking_check_ids"] = ["legal-benchmark-default-promotion-bridge"]
    signals["default_change_queue"]["status"] = "blocked"
    signals["default_change_queue"]["blocking_item_ids"] = ["default-change-legal_review"]

    checklist = ModelOpsLegalBenchmarkDefaultPromotionChecklistService().build_checklist(signals)

    assert checklist["status"] == "blocked"
    assert "cheap-first-release-decision-not-failed" in checklist["blocking_check_ids"]
    assert "default-change-queue-not-blocked" in checklist["blocking_check_ids"]
    assert checklist["checklist_rows"][0]["checklist_status"] == "blocked"
    assert "release-decision-blocked" in checklist["checklist_rows"][0]["reason_codes"]


def test_default_promotion_checklist_missing_release_or_queue_stays_review_required():
    checklist = ModelOpsLegalBenchmarkDefaultPromotionChecklistService().build_checklist(
        {"legal_benchmark_default_promotion_bridge": _ready_bridge()}
    )
    checks = {check["id"]: check for check in checklist["checks"]}

    assert checklist["status"] == "review_required"
    assert checklist["summary"]["release_decision_status"] == "not_supplied"
    assert checklist["summary"]["default_change_queue_status"] == "not_supplied"
    assert checks["cheap-first-release-decision-not-failed"]["status"] == "warn"
    assert checks["default-change-queue-not-blocked"]["status"] == "warn"
    assert checklist["checklist_rows"][0]["matched_queue_item_id"] == "not_mapped"


def test_default_promotion_checklist_redacts_sensitive_model_like_values():
    signals = _signals()
    signals["legal_benchmark_default_promotion_bridge"] = _ready_bridge("sk-" + ("c" * 24))
    signals["api_key"] = "sk-" + ("d" * 24)
    signals["raw_output"] = "RAW_PRIVATE_OUTPUT_SHOULD_NOT_LEAK"

    checklist = ModelOpsLegalBenchmarkDefaultPromotionChecklistService().build_checklist(signals)
    serialized = json.dumps(checklist, ensure_ascii=False)

    assert checklist["privacy_boundary"]["metadata_only"] is True
    assert checklist["summary"]["raw_input_field_count"] >= 2
    assert checklist["summary"]["configuration_written"] is False
    assert checklist["summary"]["network_called"] is False
    assert checklist["claim_boundary"]["automatic_default_change_claimed"] is False
    assert "redacted-sensitive-value" in serialized
    assert "RAW_PRIVATE_OUTPUT_SHOULD_NOT_LEAK" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_default_promotion_checklist_aihub_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-benchmark-default-promotion-checklist")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()["data"]
    assert direct_payload["id"] == "modelops-legal-benchmark-default-promotion-checklist"
    assert direct_payload["summary"]["network_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/legal-benchmark-default-promotion-checklist",
        json={
            "legal_benchmark_default_promotion_bridge": {
                "status": "blocked",
                "summary": {"promotion_row_count": 0},
                "blocking_check_ids": ["synthetic-bridge-block"],
                "promotion_rows": [],
            }
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["legal_benchmark_default_promotion_checklist"]["id"]
        == "modelops-legal-benchmark-default-promotion-checklist"
    )
    assert any(
        check["source_key"] == "legal_benchmark_default_promotion_checklist"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
