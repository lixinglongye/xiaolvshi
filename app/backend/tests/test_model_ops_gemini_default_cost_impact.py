import json
import re

from services.model_ops_gemini_default_cost_impact import ModelOpsGeminiDefaultCostImpactService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|password|secret|api[_-]?key|authorization|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+",
    re.IGNORECASE,
)


def test_gemini_default_cost_impact_accepts_current_agentic_default():
    impact = ModelOpsGeminiDefaultCostImpactService().build_impact(
        {
            "proposed_changes": [
                {
                    "task": "agentic",
                    "env_var": "APP_AI_AGENTIC_MODEL",
                    "current_model": "gemini-3.1-flash-lite",
                    "proposed_model": "gemini-3.1-flash-lite",
                }
            ]
        }
    )
    row = impact["impact_rows"][0]

    assert impact["status"] == "ready"
    assert impact["summary"]["estimated_monthly_delta_usd"] == 0
    assert impact["summary"]["configuration_written"] is False
    assert impact["summary"]["gateway_called"] is False
    assert impact["summary"]["network_called"] is False
    assert row["impact_status"] == "ready"
    assert row["env_var"] == "APP_AI_AGENTIC_MODEL"
    assert row["current_monthly_cost_usd"] == row["proposed_monthly_cost_usd"]
    assert row["reason_codes"] == ["cost-impact-ready"]
    assert impact["privacy_boundary"]["real_env_read"] is False
    assert not SENSITIVE_PATTERN.search(json.dumps(impact, ensure_ascii=False))


def test_gemini_default_cost_impact_requires_review_for_preview_premium_delta():
    impact = ModelOpsGeminiDefaultCostImpactService().build_impact(
        {
            "proposed_changes": [
                {
                    "task": "grounded-research",
                    "env_var": "APP_AI_GROUNDED_RESEARCH_MODEL",
                    "current_model": "gemini-3.1-flash-lite",
                    "proposed_model": "gemini-3.1-pro-preview",
                }
            ]
        }
    )
    row = impact["impact_rows"][0]

    assert impact["status"] == "review_required"
    assert impact["summary"]["premium_exception_count"] == 1
    assert impact["summary"]["estimated_monthly_delta_usd"] > 0
    assert row["impact_status"] == "review_required"
    assert row["monthly_delta_usd"] > 0
    assert "lifecycle-preview" in row["reason_codes"]
    assert "manual-premium-exception-review" in row["reason_codes"]
    assert row["release_action"] == "require_maintainer_cost_review"


def test_gemini_default_cost_impact_blocks_unknown_price_metadata():
    impact = ModelOpsGeminiDefaultCostImpactService().build_impact(
        {
            "proposed_changes": [
                {
                    "task": "fast",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "proposed_model": "gemini-9.9-flash-lite",
                }
            ]
        }
    )
    row = impact["impact_rows"][0]

    assert impact["status"] == "blocked"
    assert impact["summary"]["unknown_price_count"] == 1
    assert row["impact_status"] == "blocked"
    assert row["proposed_unit_cost_usd"] is None
    assert "proposed-price-metadata-missing" in row["reason_codes"]
    assert impact["blocking_impact_ids"] == ["gemini-default-cost-impact-fast"]


def test_gemini_default_cost_impact_route_and_models_payload_include_impact():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/gemini-default-cost-impact")
    assert response.status_code == 200
    route_payload = response.json()
    assert route_payload["success"] is True
    assert route_payload["data"]["summary"]["configuration_written"] is False

    eval_response = client.post(
        "/api/v1/aihub/models/gemini-default-cost-impact",
        json={
            "proposed_changes": [
                {
                    "task": "fast",
                    "env_var": "APP_AI_FAST_MODEL",
                    "current_model": "gemini-2.5-flash-lite",
                    "proposed_model": "gemini-2.5-flash",
                }
            ]
        },
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["data"]["status"] == "blocked"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    payload = models_response.json()
    assert payload["gemini_default_cost_impact"]["summary"]["proposal_count"] >= 2
    assert any(
        check["source_key"] == "gemini_default_cost_impact"
        for check in payload["model_ops_readiness"]["checks"]
    )
