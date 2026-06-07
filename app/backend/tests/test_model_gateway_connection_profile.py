import pytest

from services import model_gateway_connection_profile
from services.model_gateway_connection_profile import (
    ModelGatewayConnectionProfileService,
    normalize_openai_compatible_base_url,
)


def test_normalize_bare_remote_gateway_url_to_v1():
    assert normalize_openai_compatible_base_url("https://yibuapi.com") == "https://yibuapi.com/v1"
    assert normalize_openai_compatible_base_url("https://yibuapi.com/") == "https://yibuapi.com/v1"


def test_normalize_preserves_existing_openai_compatible_paths():
    assert normalize_openai_compatible_base_url("https://yibuapi.com/v1") == "https://yibuapi.com/v1"
    assert (
        normalize_openai_compatible_base_url("https://generativelanguage.googleapis.com/v1beta/openai/")
        == "https://generativelanguage.googleapis.com/v1beta/openai"
    )
    assert normalize_openai_compatible_base_url("http://127.0.0.1:8001") == "http://127.0.0.1:8001"


def test_normalize_strips_url_credentials_query_and_fragment():
    assert (
        normalize_openai_compatible_base_url("https://user:redacted@yibuapi.com?api_key=redacted-url-value#frag")
        == "https://yibuapi.com/v1"
    )


def test_connection_profile_does_not_treat_v10_as_v1():
    result = ModelGatewayConnectionProfileService().build_profile({"url": "https://yibuapi.com/v10", "key": "configured"})

    assert result["status"] == "warn"
    assert result["summary"]["v1_compatible_path"] is False
    assert "openai-compatible-v1-base-url" in result["warning_check_ids"]


def test_connection_profile_redacts_payload_key_and_recommends_v1_url(monkeypatch):
    monkeypatch.setattr(model_gateway_connection_profile.settings, "app_ai_base_url", None)
    monkeypatch.setattr(model_gateway_connection_profile.settings, "app_ai_key", None)

    result = ModelGatewayConnectionProfileService().build_profile(
        {
            "url": "https://yibuapi.com",
            "key": "redacted-local-key-value",
        }
    )

    rendered = str(result)
    assert result["status"] == "pass"
    assert result["summary"]["base_url_was_normalized"] is True
    assert result["summary"]["remote_bare_url_normalized_to_v1"] is True
    assert result["summary"]["api_key_configured"] is True
    assert result["connection"]["normalized_base_url_display"] == "https://yibuapi.com/v1"
    assert result["connection"]["api_key_display"] == "{{APP_AI_KEY}}"
    assert result["privacy_boundary"]["credentials_included"] is False
    assert result["claim_boundary"]["actual_api_key_validated"] is False
    assert "redacted-local-key-value" not in rendered


def test_connection_profile_blocks_credentials_in_url():
    result = ModelGatewayConnectionProfileService().build_profile(
        {
            "url": "https://user:redacted@yibuapi.com?api_key=redacted-url-value",
        }
    )

    rendered = str(result)
    assert result["status"] == "fail"
    assert "base-url-no-credentials" in result["blocking_check_ids"]
    assert "runtime-normalization-boundary" in result["blocking_check_ids"]
    assert "redacted-url-value" not in rendered
    assert "user:redacted" not in rendered


def test_connection_profile_warns_when_configuration_missing(monkeypatch):
    monkeypatch.setattr(model_gateway_connection_profile.settings, "app_ai_base_url", None)
    monkeypatch.setattr(model_gateway_connection_profile.settings, "app_ai_key", None)

    result = ModelGatewayConnectionProfileService().build_profile()

    assert result["status"] == "warn"
    assert "base-url-configured" in result["warning_check_ids"]
    assert "api-key-configured" in result["warning_check_ids"]
    assert result["recommended_env"]["APP_AI_BASE_URL"] == "https://yibuapi.com/v1"
    assert result["summary"]["cheap_first_ready_count"] >= 5


def test_connection_profile_route_includes_metadata_only_profile():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models/gateway-connection-profile")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["id"] == "model-gateway-connection-profile"
    assert payload["privacy_boundary"]["gateway_called"] is False
    assert payload["summary"]["credentials_included"] is False
