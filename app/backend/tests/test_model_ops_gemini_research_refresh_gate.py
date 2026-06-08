from __future__ import annotations

import json
import re

from services.model_ops_gemini_research_refresh_gate import ModelOpsGeminiResearchRefreshGateService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|authorization|password|secret|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_gemini_research_refresh_gate_builds_source_backed_review_plan():
    gate = ModelOpsGeminiResearchRefreshGateService().build_gate()
    source_ids = {row["id"] for row in gate["research_source_rows"]}
    adoption_rows = {row["task"]: row for row in gate["adoption_rows"]}

    assert gate["id"] == "modelops-gemini-research-refresh-gate"
    assert gate["status"] == "review_required"
    assert gate["summary"]["research_source_count"] == 5
    assert gate["summary"]["official_source_count"] == 3
    assert gate["summary"]["public_benchmark_source_count"] == 2
    assert gate["summary"]["adoption_task_count"] == 5
    assert gate["summary"]["cheap_first_task_count"] == 3
    assert gate["summary"]["public_benchmark_license_review_count"] == 5
    assert gate["summary"]["external_refresh_completed"] is False
    assert gate["summary"]["public_benchmark_downloaded"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["configuration_written"] is False

    assert source_ids == {
        "gemini-api-models",
        "gemini-api-pricing",
        "gemini-openai-compatible",
        "legalbench",
        "cuad",
    }
    assert adoption_rows["fast"]["route_mode"] == "cheap_first"
    assert adoption_rows["fast"]["default_model"] == "gemini-2.5-flash-lite"
    assert adoption_rows["fast"]["cheap_first_aligned"] is True
    assert adoption_rows["fast"]["required_source_ids"] == [
        "gemini-api-models",
        "gemini-api-pricing",
        "legalbench",
    ]
    assert adoption_rows["ocr"]["required_source_ids"] == [
        "gemini-api-models",
        "gemini-api-pricing",
        "cuad",
    ]
    assert adoption_rows["review"]["route_mode"] == "cheap_precheck_then_balanced"
    assert adoption_rows["pdf"]["release_action"] == "maintainer_review"
    assert "route_exception_review" in adoption_rows["pdf"]["reason_codes"]


def test_gemini_research_refresh_gate_links_upstream_modelops_signals():
    gate = ModelOpsGeminiResearchRefreshGateService().build_gate()
    check_ids = {check["id"]: check for check in gate["checks"]}

    assert check_ids["official-gemini-sources-present"]["status"] == "pass"
    assert check_ids["public-legal-benchmark-sources-present"]["status"] == "pass"
    assert check_ids["route-preflight-linked"]["status"] == "pass"
    assert check_ids["legal-micro-benchmark-linked"]["status"] == "pass"
    assert check_ids["legal-risk-bridge-linked"]["status"] == "pass"
    assert check_ids["adoption-review-boundary"]["status"] == "warn"
    assert "adoption-review-boundary" in gate["warning_check_ids"]
    assert gate["blocking_check_ids"] == []
    assert gate["source_signal_summary"]["gemini_cheap_first_route_preflight_status"] == "review_required"
    assert gate["source_signal_summary"]["legal_micro_benchmark_preflight_status"] == "ready"
    assert gate["source_signal_summary"]["legal_benchmark_risk_bridge_status"] == "review_required"


def test_gemini_research_refresh_gate_privacy_and_claim_boundaries_do_not_leak_payloads():
    gate = ModelOpsGeminiResearchRefreshGateService().build_gate(
        {
            "observed_models": [
                "models/gemini-2.5-flash-lite",
                "sk-THIS_SHOULD_NOT_BE_ECHOED_123456789012345",
                "client@example.test",
            ],
            "headers": {"Authorization": "Bearer TEST_TOKEN"},
            "prompt": "raw prompt body",
            "raw_model_output": "raw output body",
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["returns_benchmark_samples"] is False
    assert gate["privacy_boundary"]["returns_public_dataset_rows"] is False
    assert gate["privacy_boundary"]["returns_raw_legal_text"] is False
    assert gate["privacy_boundary"]["returns_prompts"] is False
    assert gate["privacy_boundary"]["returns_raw_model_output"] is False
    assert gate["privacy_boundary"]["returns_gateway_payloads"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert gate["claim_boundary"]["public_benchmark_scores_claimed"] is False
    assert gate["claim_boundary"]["default_model_changed"] is False
    assert gate["claim_boundary"]["all_gemini_models_supported_claimed"] is False
    assert "THIS_SHOULD_NOT_BE_ECHOED" not in serialized
    assert "client@example.test" not in serialized
    assert "Bearer TEST_TOKEN" not in serialized
    assert "raw prompt body" not in serialized
    assert "raw output body" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_research_refresh_gate_route_and_modelops_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-research-refresh-gate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-gemini-research-refresh-gate"
    assert payload["data"]["summary"]["research_source_count"] == 5
    assert payload["data"]["summary"]["gateway_called"] is False

    posted = client.post(
        "/api/v1/aihub/models/gemini-research-refresh-gate",
        json={"observed_models": ["google/gemini-2.5-flash-lite"]},
    )
    assert posted.status_code == 200
    assert posted.json()["data"]["privacy_boundary"]["metadata_only"] is True
    assert posted.json()["data"]["summary"]["network_called"] is False

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["gemini_research_refresh_gate"]["id"] == "modelops-gemini-research-refresh-gate"
    assert any(
        check["source_key"] == "gemini_research_refresh_gate"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
