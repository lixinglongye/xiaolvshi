import json
import re

from services.model_ops_gemini_official_lifecycle_drift_gate import (
    ModelOpsGeminiOfficialLifecycleDriftGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"\bsk-[A-Za-z0-9_-]*[0-9][A-Za-z0-9_-]{20,}\b|authorization|bearer|password|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_gemini_official_lifecycle_drift_gate_tracks_defaults_and_reviews():
    gate = ModelOpsGeminiOfficialLifecycleDriftGateService().build_gate()
    checks = {check["id"]: check for check in gate["checks"]}
    defaults = {row["task"]: row for row in gate["default_task_rows"]}
    lifecycle_rows = {row["model_id"]: row for row in gate["lifecycle_rows"]}

    assert gate["id"] == "modelops-gemini-official-lifecycle-drift-gate"
    assert gate["status"] == "review_required"
    assert gate["summary"]["tracked_model_count"] >= 12
    assert gate["summary"]["high_frequency_task_count"] == 4
    assert gate["summary"]["stable_flash_lite_default_count"] == 4
    assert gate["summary"]["review_default_count"] == 2
    assert gate["summary"]["blocked_default_count"] == 0
    assert gate["summary"]["gateway_called"] is False
    assert checks["high-frequency-text-defaults-stable-flash-lite"]["status"] == "pass"
    assert checks["review-lifecycle-defaults-visible"]["status"] == "warn"
    assert "catalog-lifecycle-drift-visible" in gate["warning_check_ids"]

    for task in ("cheap", "fast", "classification", "ocr"):
        assert defaults[task]["canonical_model"] == "gemini-2.5-flash-lite"
        assert defaults[task]["stable_flash_lite_aligned"] is True
        assert defaults[task]["blocked_default"] is False

    assert defaults["agentic"]["canonical_model"] == "gemini-3.1-flash-lite"
    assert defaults["agentic"]["requires_review"] is True
    assert lifecycle_rows["gemini-3.1-flash-lite"]["official_lifecycle"] == "gateway_observed_review"
    assert lifecycle_rows["gemini-3.1-flash-lite"]["drift_status"] == "catalog_marks_review_model_stable"


def test_gemini_official_lifecycle_drift_gate_blocks_deprecated_default_override():
    gate = ModelOpsGeminiOfficialLifecycleDriftGateService().build_gate(
        {
            "official_lifecycle_snapshot": [
                {
                    "model_id": "gemini-2.5-flash-lite",
                    "official_lifecycle": "deprecated",
                    "default_policy": "blocked_from_defaults",
                    "default_allowed_for_high_frequency": False,
                    "required_action": "Remove from defaults until a maintainer refreshes the official source review.",
                }
            ]
        }
    )
    checks = {check["id"]: check for check in gate["checks"]}

    assert gate["status"] == "blocked"
    assert gate["summary"]["blocked_default_count"] == 4
    assert checks["high-frequency-text-defaults-stable-flash-lite"]["status"] == "fail"
    assert checks["preview-deprecated-shutdown-defaults-blocked"]["status"] == "fail"
    assert "preview-deprecated-shutdown-defaults-blocked" in gate["blocking_check_ids"]
    assert any("Do not promote Gemini/NewAPI default changes" in action for action in gate["recommended_actions"])


def test_gemini_official_lifecycle_drift_gate_accepts_sanitized_task_defaults():
    gate = ModelOpsGeminiOfficialLifecycleDriftGateService().build_gate(
        {"task_defaults": {"fast": "gemini-3-flash-preview"}}
    )
    checks = {check["id"]: check for check in gate["checks"]}
    defaults = {row["task"]: row for row in gate["default_task_rows"]}

    assert gate["status"] == "blocked"
    assert defaults["fast"]["canonical_model"] == "gemini-3-flash-preview"
    assert defaults["fast"]["official_lifecycle"] == "preview"
    assert defaults["fast"]["blocked_default"] is True
    assert checks["high-frequency-text-defaults-stable-flash-lite"]["status"] == "fail"


def test_gemini_official_lifecycle_drift_gate_boundaries_are_metadata_only():
    gate = ModelOpsGeminiOfficialLifecycleDriftGateService().build_gate()
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["network_called"] is False
    assert gate["privacy_boundary"]["gateway_called"] is False
    assert gate["privacy_boundary"]["configuration_written"] is False
    assert gate["privacy_boundary"]["credentials_included"] is False
    assert gate["privacy_boundary"]["request_bodies_included"] is False
    assert gate["privacy_boundary"]["response_bodies_included"] is False
    assert gate["privacy_boundary"]["raw_payload_echoed"] is False
    assert gate["privacy_boundary"]["raw_model_output_included"] is False
    assert gate["claim_boundary"]["all_gemini_models_supported_claimed"] is False
    assert gate["claim_boundary"]["live_gateway_execution_claimed"] is False
    assert gate["claim_boundary"]["automatic_default_change_claimed"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_official_lifecycle_drift_gate_route_and_aggregate_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-official-lifecycle-drift-gate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-gemini-official-lifecycle-drift-gate"
    assert payload["data"]["summary"]["network_called"] is False

    post_response = client.post(
        "/api/v1/aihub/models/gemini-official-lifecycle-drift-gate",
        json={"task_defaults": {"fast": "gemini-3-flash-preview"}},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["gemini_official_lifecycle_drift_gate"]["id"]
        == "modelops-gemini-official-lifecycle-drift-gate"
    )
    assert any(
        check["source_key"] == "gemini_official_lifecycle_drift_gate"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
