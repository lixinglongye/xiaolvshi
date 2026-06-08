import json
import re

import pytest

from services.model_ops_newapi_channel_bootstrap import ModelOpsNewapiChannelBootstrapService


SENSITIVE_PATTERN = re.compile(r"sk-[A-Za-z0-9]{8,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", re.IGNORECASE)


def test_newapi_channel_bootstrap_normalizes_yibuapi_and_redacts_key():
    secret = "s" + "k-" + ("B" * 24)
    result = ModelOpsNewapiChannelBootstrapService().build_packet(
        {
            "_type": "newapi_channel_conn",
            "url": "https://yibuapi.com",
            "key": secret,
            "observed_models": ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"],
        }
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["id"] == "modelops-newapi-channel-bootstrap"
    assert result["status"] == "warn"
    assert result["summary"]["channel_url_configured"] is True
    assert result["summary"]["channel_key_present"] is True
    assert result["summary"]["normalized_base_url"] == "https://yibuapi.com/v1"
    assert result["summary"]["remote_bare_url_normalized_to_v1"] is True
    assert result["channel"]["provider_family"] == "newapi-yibuapi"
    assert result["channel"]["api_key_display"] == "{{APP_AI_KEY}}"
    assert result["recommended_env"]["APP_AI_BASE_URL"] == "https://yibuapi.com/v1"
    assert result["recommended_env"]["APP_AI_KEY"] == "{{APP_AI_KEY}}"
    assert result["recommended_env"]["APP_AI_CHEAP_MODEL"] == "gemini-2.5-flash-lite"
    assert result["summary"]["cheap_first_ready_count"] >= 4
    assert result["summary"]["premium_exception_review_count"] == 1
    assert result["summary"]["configuration_written"] is False
    assert result["summary"]["gateway_called"] is False
    assert result["summary"]["network_called"] is False
    assert result["privacy_boundary"]["credentials_included"] is False
    assert result["claim_boundary"]["actual_key_validated"] is False
    assert secret not in rendered
    safe_rendered = (
        rendered.replace("{{APP_AI_KEY}}", "")
        .replace("APP_AI_KEY", "")
        .replace("api_key_display", "")
        .replace("api_key_env", "")
    )
    assert not SENSITIVE_PATTERN.search(safe_rendered)


def test_newapi_channel_bootstrap_blocks_secret_material_in_url():
    result = ModelOpsNewapiChannelBootstrapService().build_packet(
        {
            "url": "https://user:redacted@yibuapi.com?api_key=redacted-url-value",
            "observed_models": ["models/gemini-2.5-pro"],
        }
    )
    rendered = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "fail"
    assert "channel-secret-redacted" in result["blocking_check_ids"]
    assert result["channel"]["normalized_base_url_display"] == "https://yibuapi.com/v1"
    assert result["privacy_boundary"]["raw_payload_echoed"] is False
    assert "redacted-url-value" not in rendered
    assert "user:redacted" not in rendered


def test_newapi_channel_bootstrap_route_returns_metadata_only_packet():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post(
        "/api/v1/aihub/models/newapi-channel-bootstrap",
        json={"url": "https://yibuapi.com", "key": "configured", "observed_models": ["gemini-2.5-flash-lite"]},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["id"] == "modelops-newapi-channel-bootstrap"
    assert payload["summary"]["normalized_base_url"] == "https://yibuapi.com/v1"
    assert payload["summary"]["gateway_called"] is False
    assert payload["summary"]["network_called"] is False
    assert payload["channel"]["api_key_display"] == "{{APP_AI_KEY}}"


def test_newapi_channel_bootstrap_get_route_is_in_model_ops_aggregate():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    direct = client.get("/api/v1/aihub/models/newapi-channel-bootstrap")
    aggregate = client.get("/api/v1/aihub/models")

    assert direct.status_code == 200
    assert aggregate.status_code == 200
    assert direct.json()["data"]["id"] == "modelops-newapi-channel-bootstrap"
    assert aggregate.json()["newapi_channel_bootstrap"]["id"] == "modelops-newapi-channel-bootstrap"
