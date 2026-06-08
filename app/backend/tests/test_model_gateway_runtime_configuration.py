import pytest

from services import model_gateway_runtime_configuration
from services.model_gateway_runtime_configuration import ModelGatewayRuntimeConfigurationService


def test_runtime_configuration_uses_yibuapi_v1_and_placeholders(monkeypatch):
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_key", "local-secret-value")

    result = ModelGatewayRuntimeConfigurationService().build_configuration()
    rendered = str(result)

    assert result["status"] == "pass"
    assert result["summary"]["base_url_configured"] is True
    assert result["summary"]["api_key_configured"] is True
    assert result["summary"]["openai_compatible_path"] is True
    assert result["runtime_env"]["base_url_display"] == "https://yibuapi.com/v1"
    assert result["runtime_env"]["api_key_display"] == "{{APP_AI_KEY}}"
    assert result["summary"]["cheap_first_ready_count"] >= 4
    assert result["runtime_probe_sequence"][0]["step"] == "list-models"
    assert result["runtime_probe_sequence"][1]["model"] == "gemini-2.5-flash-lite"
    assert result["privacy_boundary"]["credentials_included"] is False
    assert result["claim_boundary"]["actual_key_validated"] is False
    assert "local-secret-value" not in rendered
    assert "sk-" not in rendered


def test_runtime_configuration_normalizes_bare_remote_gateway(monkeypatch):
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_base_url", "https://yibuapi.com")
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_key", "configured")

    result = ModelGatewayRuntimeConfigurationService().build_configuration()

    assert result["status"] == "pass"
    assert result["summary"]["normalized_base_url"] == "https://yibuapi.com/v1"
    assert result["runtime_env"]["client_base_url_source"] == "normalize_openai_compatible_base_url(APP_AI_BASE_URL)"


def test_runtime_configuration_blocks_credentials_in_url(monkeypatch):
    monkeypatch.setattr(
        model_gateway_runtime_configuration.settings,
        "app_ai_base_url",
        "https://user:redacted@yibuapi.com?api_key=redacted-url-value",
    )
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_key", "configured")

    result = ModelGatewayRuntimeConfigurationService().build_configuration()
    rendered = str(result)

    assert result["status"] == "fail"
    assert "runtime-base-url-no-credential-material" in result["blocking_check_ids"]
    assert result["summary"]["normalized_base_url"] == "https://yibuapi.com/v1"
    assert "user:redacted" not in rendered
    assert "redacted-url-value" not in rendered


def test_runtime_configuration_warns_when_env_missing(monkeypatch):
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_base_url", None)
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_key", None)

    result = ModelGatewayRuntimeConfigurationService().build_configuration()

    assert result["status"] == "warn"
    assert "runtime-base-url-configured" in result["warning_check_ids"]
    assert "runtime-api-key-placeholder" in result["warning_check_ids"]
    assert result["runtime_env"]["api_key_display"] == "not_configured"


def test_runtime_configuration_blocks_high_frequency_premium_drift(monkeypatch):
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_base_url", "https://yibuapi.com/v1")
    monkeypatch.setattr(model_gateway_runtime_configuration.settings, "app_ai_key", "configured")
    monkeypatch.setattr(model_gateway_runtime_configuration, "task_default_model", lambda task: "gemini-2.5-pro")

    result = ModelGatewayRuntimeConfigurationService().build_configuration()
    fast_row = next(row for row in result["role_rows"] if row["role"] == "fast")

    assert result["status"] == "fail"
    assert "runtime-cheap-first-role-defaults" in result["blocking_check_ids"]
    assert fast_row["high_frequency_role"] is True
    assert fast_row["cheap_first_ready"] is False


def test_runtime_configuration_route_returns_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models/gateway-runtime-configuration")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["id"] == "model-gateway-runtime-configuration"
    assert payload["privacy_boundary"]["gateway_called"] is False
    assert payload["summary"]["credentials_included"] is False
