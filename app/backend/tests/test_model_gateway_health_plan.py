from services import model_gateway_health_plan
from services.model_gateway_health_plan import ModelGatewayHealthPlanService


def test_gateway_health_plan_uses_placeholders_and_cheap_probe(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "local-secret-value")

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "pass"
    assert plan["summary"]["base_url_configured"] is True
    assert plan["summary"]["api_key_configured"] is True
    assert plan["gateway_config"]["api_key_display"] == "{{APP_AI_KEY}}"
    assert plan["dry_run_contracts"][0]["url"] == "https://yibuapi.com/v1/models"
    assert plan["dry_run_contracts"][1]["body"]["model"] == "gemini-2.5-flash-lite"
    assert "local-secret-value" not in str(plan)
    assert "sk-" not in str(plan)


def test_gateway_health_plan_warns_when_secret_setup_is_missing(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", None)
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", None)

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "warn"
    assert "base-url-configured" in plan["warning_check_ids"]
    assert "api-key-configured" in plan["warning_check_ids"]
    assert plan["dry_run_contracts"][0]["url"] == "{{APP_AI_BASE_URL}}/models"


def test_gateway_health_plan_blocks_public_http_gateway(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "http://example.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured")

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "fail"
    assert "https-base-url" in plan["blocking_check_ids"]


def test_gateway_health_plan_warns_unknown_gateway_models(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured")
    monkeypatch.setattr(model_gateway_health_plan, "cheap_text_model", lambda: "newapi/gemini-custom-cheap")
    monkeypatch.setattr(model_gateway_health_plan, "task_default_model", lambda task: "newapi/gemini-custom-cheap")

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "warn"
    assert "cheap-first-known-models" in plan["warning_check_ids"]
    assert plan["summary"]["unknown_role_count"] >= 1


def test_model_ops_route_includes_gateway_health_plan():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["gateway_health_plan"]["status"] in {"pass", "warn", "fail"}
    assert any(check["source_key"] == "gateway_health_plan" for check in payload["model_ops_readiness"]["checks"])
