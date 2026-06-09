from services import model_gateway_health_plan
from services.model_gateway_health_plan import ModelGatewayHealthPlanService


def test_gateway_health_plan_uses_placeholders_and_cheap_probe(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "local-secret-value")

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "pass"
    assert plan["summary"]["base_url_configured"] is True
    assert plan["summary"]["api_key_configured"] is True
    assert plan["summary"]["known_media_role_count"] == 1
    assert plan["gateway_config"]["api_key_display"] == "{{APP_AI_KEY}}"
    assert plan["dry_run_contracts"][0]["url"] == "https://yibuapi.com/v1/models"
    assert plan["dry_run_contracts"][1]["body"]["model"] == "gemini-2.5-flash-lite"
    assert plan["dry_run_contracts"][2]["id"] == "image-generation-smoke"
    assert plan["dry_run_contracts"][2]["body"]["model"] == "gemini-2.5-flash-image"
    image_role = next(row for row in plan["role_models"] if row["role"] == "image")
    assert image_role["billing_unit"] == "image"
    assert image_role["probe_type"] == "image-generation"
    assert image_role["estimated_probe_cost_usd"] == 0.039
    assert image_role["output_usd_per_image"] == 0.039
    assert "image-probe-priced-model" not in plan["blocking_check_ids"]
    assert "local-secret-value" not in str(plan)
    assert "sk-" not in str(plan)


def test_gateway_health_plan_normalizes_bare_remote_gateway_url(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured")

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "pass"
    assert plan["summary"]["normalized_base_url"] == "https://yibuapi.com/v1"
    assert plan["dry_run_contracts"][0]["url"] == "https://yibuapi.com/v1/models"
    assert plan["dry_run_contracts"][1]["url"] == "https://yibuapi.com/v1/chat/completions"


def test_gateway_health_plan_does_not_treat_v10_as_v1(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v10")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured")

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "warn"
    assert "v1-path-shape" in plan["warning_check_ids"]


def test_gateway_health_plan_strips_url_credentials_from_dry_run(monkeypatch):
    monkeypatch.setattr(
        model_gateway_health_plan.settings,
        "app_ai_base_url",
        "https://user:redacted@yibuapi.com?api_key=redacted-url-value",
    )
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured")

    plan = ModelGatewayHealthPlanService().build_plan()
    rendered = str(plan)

    assert plan["summary"]["normalized_base_url"] == "https://yibuapi.com/v1"
    assert plan["dry_run_contracts"][0]["url"] == "https://yibuapi.com/v1/models"
    assert "user:redacted" not in rendered
    assert "redacted-url-value" not in rendered


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


def test_gateway_health_plan_blocks_unpriced_image_default(monkeypatch):
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_key", "configured")
    monkeypatch.setattr(model_gateway_health_plan.settings, "app_ai_image_model", "newapi/gemini-custom-image")

    plan = ModelGatewayHealthPlanService().build_plan()

    assert plan["status"] == "fail"
    assert "image-probe-priced-model" in plan["blocking_check_ids"]
    image_role = next(row for row in plan["role_models"] if row["role"] == "image")
    assert image_role["cost_tier"] is None
    assert image_role["is_known_model"] is False
    assert image_role["output_usd_per_image"] is None


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
