import json
import re

from services.model_ops_gemini_cheap_first_route_preflight import (
    ModelOpsGeminiCheapFirstRoutePreflightService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|authorization|password|secret|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_gemini_cheap_first_route_preflight_builds_reviewable_plan():
    preflight = ModelOpsGeminiCheapFirstRoutePreflightService().build_preflight()
    route_rows = {row["task"]: row for row in preflight["route_task_rows"]}
    variant_rows = {row["model_id"]: row for row in preflight["variant_preflight_rows"]}

    assert preflight["id"] == "modelops-gemini-cheap-first-route-preflight"
    assert preflight["status"] == "review_required"
    assert preflight["summary"]["official_source_count"] == 4
    assert preflight["summary"]["route_task_count"] == 11
    assert preflight["summary"]["cheap_first_route_count"] == 7
    assert preflight["summary"]["balanced_route_count"] == 2
    assert preflight["summary"]["premium_exception_count"] == 2
    assert preflight["summary"]["catalog_model_count"] >= 10
    assert preflight["summary"]["variant_row_count"] >= 10
    assert preflight["summary"]["default_allowed_variant_count"] >= 2
    assert preflight["summary"]["model_called"] is False
    assert preflight["summary"]["gateway_called"] is False
    assert preflight["summary"]["network_called"] is False
    assert preflight["summary"]["configuration_written"] is False
    assert preflight["summary"]["credentials_included"] is False
    assert preflight["blocking_check_ids"] == []
    assert "preview-premium-review-boundary" in preflight["warning_check_ids"]

    assert route_rows["fast"]["default_model"] == "gemini-2.5-flash-lite"
    assert route_rows["fast"]["route_mode"] == "cheap_first"
    assert route_rows["fast"]["cheap_first_aligned"] is True
    assert route_rows["fast"]["release_action"] == "keep_default_route"
    assert route_rows["ocr"]["canonical_model"] == "gemini-2.5-flash-lite"
    assert route_rows["agentic"]["default_model"] == "gemini-3.1-flash-lite"
    assert route_rows["grounded-research"]["default_model"] == "gemini-3.1-flash-lite"
    assert route_rows["embedding"]["default_model"] == "gemini-embedding-001"
    assert route_rows["embedding"]["cheap_first_aligned"] is True
    assert route_rows["embedding"]["default_allowed_without_review"] is True
    assert route_rows["review"]["route_mode"] == "cheap_precheck_then_balanced"
    assert route_rows["pdf"]["premium_exception_required"] is True
    assert route_rows["pdf"]["release_action"] == "require_operator_exception"
    assert route_rows["image"]["premium_exception_required"] is True

    assert variant_rows["gemini-2.5-flash-lite"]["default_allowed_without_review"] is True
    assert variant_rows["gemini-3.1-flash-lite"]["default_allowed_without_review"] is True
    assert variant_rows["gemini-2.5-pro"]["default_promotion_state"] == "review_required"
    assert "premium_exception_review" in variant_rows["gemini-2.5-pro"]["reason_codes"]
    assert variant_rows["gemini-3-pro-image"]["default_promotion_state"] == "blocked"
    assert "pricing_missing" in variant_rows["gemini-3-pro-image"]["reason_codes"]


def test_gemini_cheap_first_route_preflight_links_official_sources_and_signals():
    preflight = ModelOpsGeminiCheapFirstRoutePreflightService().build_preflight()

    source_ids = {row["id"] for row in preflight["official_source_rows"]}
    assert source_ids == {
        "gemini-api-models",
        "gemini-api-pricing",
        "gemini-openai-compatible",
        "vertex-ai-model-versions",
    }
    assert preflight["source_signal_summary"]["gemini_variant_matrix_status"] == "review_required"
    assert preflight["source_signal_summary"]["gemini_alias_capability_status"] == "ready"
    assert preflight["source_signal_summary"]["gemini_cheap_first_coverage_status"] == "review_required"
    assert preflight["validation_commands"][0].startswith(
        "python -m pytest tests/test_model_ops_gemini_cheap_first_route_preflight.py"
    )
    assert "npm run ui:regression" in preflight["validation_commands"]


def test_gemini_cheap_first_route_preflight_boundaries_do_not_leak_sensitive_data():
    preflight = ModelOpsGeminiCheapFirstRoutePreflightService().build_preflight(
        {
            "observed_models": [
                "models/gemini-2.5-flash-lite",
                "sk-THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED_123456789",
                "client@example.com",
            ]
        }
    )
    serialized = json.dumps(preflight, ensure_ascii=False)

    assert preflight["privacy_boundary"]["metadata_only"] is True
    assert preflight["privacy_boundary"]["model_called"] is False
    assert preflight["privacy_boundary"]["gateway_called"] is False
    assert preflight["privacy_boundary"]["network_called"] is False
    assert preflight["privacy_boundary"]["configuration_written"] is False
    assert preflight["privacy_boundary"]["returns_credentials"] is False
    assert preflight["privacy_boundary"]["returns_api_key"] is False
    assert preflight["claim_boundary"]["live_gateway_execution_claimed"] is False
    assert preflight["claim_boundary"]["automatic_default_change_claimed"] is False
    assert "THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED" not in serialized
    assert "client@example.com" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_gemini_cheap_first_route_preflight_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-cheap-first-route-preflight")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-gemini-cheap-first-route-preflight"
    assert payload["data"]["summary"]["route_task_count"] == 11
    assert payload["data"]["summary"]["gateway_called"] is False

    posted = client.post(
        "/api/v1/aihub/models/gemini-cheap-first-route-preflight",
        json={"observed_models": ["google/gemini-2.5-flash-lite"]},
    )
    assert posted.status_code == 200
    assert posted.json()["data"]["summary"]["observed_model_count"] >= 1
    assert posted.json()["data"]["privacy_boundary"]["returns_request_body"] is False
    assert posted.json()["data"]["privacy_boundary"]["returns_response_body"] is False

    forbidden_posted = client.post(
        "/api/v1/aihub/models/gemini-cheap-first-route-preflight",
        json={
            "observed_models": ["models/gemini-2.5-flash-lite", "client@example.test"],
            "headers": {"Authorization": "Bearer TEST_TOKEN"},
            "prompt": "copied prompt body",
            "raw_model_output": "copied output",
        },
    )
    forbidden_serialized = json.dumps(forbidden_posted.json(), ensure_ascii=False)
    assert forbidden_posted.status_code == 200
    assert forbidden_posted.json()["data"]["summary"]["raw_payload_echoed"] is False
    assert forbidden_posted.json()["data"]["privacy_boundary"]["returns_headers"] is False
    assert forbidden_posted.json()["data"]["privacy_boundary"]["returns_raw_prompt"] is False
    assert forbidden_posted.json()["data"]["privacy_boundary"]["returns_raw_model_output"] is False
    assert "client@example.test" not in forbidden_serialized
    assert "Bearer TEST_TOKEN" not in forbidden_serialized
    assert "copied prompt body" not in forbidden_serialized
    assert "copied output" not in forbidden_serialized

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["gemini_cheap_first_route_preflight"]["id"]
        == "modelops-gemini-cheap-first-route-preflight"
    )
    assert any(
        check["source_key"] == "gemini_cheap_first_route_preflight"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
