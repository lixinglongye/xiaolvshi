import pytest

from services import model_gateway_probe_evaluation
from services.model_gateway_probe_evaluation import (
    REDACTED_MODEL_ID,
    ModelGatewayProbeEvaluationService,
    model_gateway_probe_evaluation_registry,
)
from services.model_gateway_live_probe import ModelGatewayLiveProbeService


@pytest.fixture(autouse=True)
def clear_gateway_probe_registry():
    model_gateway_probe_evaluation_registry.clear()
    yield
    model_gateway_probe_evaluation_registry.clear()


def test_gateway_probe_evaluation_recommends_cheap_first_models():
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {
                "data": [
                    {"id": "models/gemini-2.5-flash-lite"},
                    {"id": "gemini-2.5-flash"},
                    {"id": "gemini-3.1-flash-lite"},
                    {"id": "gemini-2.5-pro"},
                    {"id": "gemini-2.5-flash-image"},
                ]
            },
            "chat_probe_results": {
                "models/gemini-2.5-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 900},
                "gemini-2.5-flash": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 1200},
                "gemini-3.1-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 1000},
            },
            "image_probe_results": {
                "gemini-2.5-flash-image": {"status": "pass", "http_status": 200, "image_count": 1, "latency_ms": 2400}
            },
        }
    )

    assert result["status"] == "pass"
    assert result["summary"]["cheap_candidate_count"] >= 1
    assert result["summary"]["probed_cheap_candidate_count"] >= 1
    assert result["summary"]["image_candidate_count"] == 1
    assert result["summary"]["probed_image_candidate_count"] == 1
    recommended_env = {row["env_var"]: row["recommended_value"] for row in result["recommended_env"]}
    assert recommended_env["APP_AI_CHEAP_MODEL"] == "models/gemini-2.5-flash-lite"
    assert recommended_env["APP_AI_GROUNDED_RESEARCH_MODEL"] == "gemini-3.1-flash-lite"
    assert recommended_env["APP_AI_AGENTIC_MODEL"] == "gemini-3.1-flash-lite"
    assert recommended_env["APP_AI_IMAGE_MODEL"] == "gemini-2.5-flash-image"
    image_row = next(row for row in result["model_rows"] if row["canonical_model"] == "gemini-2.5-flash-image")
    assert image_row["image_probe_status"] == "pass"
    assert image_row["image_count"] == 1
    assert image_row["output_usd_per_image"] == 0.039
    assert "sk-" not in str(result)


def test_gateway_probe_evaluation_warns_unknown_gemini_and_missing_probe():
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {
                "data": [
                    {"id": "gemini-2.5-flash-lite"},
                    {"id": "newapi/gemini-custom-cheap"},
                ]
            }
        }
    )

    assert result["status"] == "warn"
    assert "cheap-chat-probe-passed" in result["warning_check_ids"]
    assert "unknown-gemini-catalog-review" in result["warning_check_ids"]
    assert result["summary"]["unknown_gemini_count"] == 1


def test_gateway_probe_evaluation_fails_without_known_low_cost_candidate():
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {"data": [{"id": "provider/non-gemini"}]},
            "chat_probe_results": {"provider/non-gemini": {"status": "pass", "http_status": 200, "json_ok": True}},
        }
    )

    assert result["status"] == "fail"
    assert "cheap-first-candidate-present" in result["blocking_check_ids"]


def test_gateway_probe_evaluation_warns_failed_probe():
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "model_ids": ["gemini-2.5-flash-lite", "gemini-2.5-flash"],
            "chat_probe_results": {
                "gemini-2.5-flash-lite": {"http_status": 500, "json_ok": False},
                "gemini-2.5-flash": {"http_status": 200, "json_ok": True},
            },
        }
    )

    assert result["status"] == "warn"
    assert "no-failed-probes" in result["warning_check_ids"]
    assert any(row["chat_probe_status"] == "fail" for row in result["model_rows"])


def test_gateway_probe_evaluation_warns_failed_image_probe():
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "model_ids": ["gemini-2.5-flash-lite", "gemini-2.5-flash-image"],
            "chat_probe_results": {"gemini-2.5-flash-lite": {"http_status": 200, "json_ok": True}},
            "image_probe_results": {"gemini-2.5-flash-image": {"http_status": 500, "image_count": 0}},
        }
    )

    assert result["status"] == "warn"
    assert "no-failed-image-probes" in result["warning_check_ids"]
    image_row = next(row for row in result["model_rows"] if row["canonical_model"] == "gemini-2.5-flash-image")
    assert image_row["image_probe_status"] == "fail"


def test_gateway_probe_evaluation_blocks_raw_image_or_prompt_payload_fields():
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {"data": [{"id": "gemini-2.5-flash-lite"}]},
            "chat_probe_results": {
                "gemini-2.5-flash-lite": {
                    "status": "pass",
                    "http_status": 200,
                    "json_ok": True,
                    "prompt": "raw user prompt must not be submitted",
                }
            },
            "image_probe_results": {
                "gemini-2.5-flash-image": {
                    "status": "pass",
                    "http_status": 200,
                    "image_count": 1,
                    "image_url": "https://example.invalid/generated.png",
                }
            },
        }
    )

    assert result["status"] == "fail"
    assert "sanitized-payload-fields" in result["blocking_check_ids"]
    assert result["summary"]["forbidden_payload_field_count"] == 2
    assert "raw user prompt" not in str(result)
    assert "generated.png" not in str(result)


def test_gateway_probe_evaluation_blocks_secret_like_values_without_echoing_them():
    secret_value = "s" + "k-" + ("A" * 24)
    bearer_value = "Bearer " + ("token_" * 4)
    email_value = "ops" + "@" + "example.test"
    data_uri_value = "data:image/png;" + "base64," + ("A" * 16)
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {
                "data": [
                    {"id": "gemini-2.5-flash-lite", "owner": email_value},
                    {"id": "gemini-2.5-flash-image"},
                ]
            },
            "chat_probe_results": {
                "gemini-2.5-flash-lite": {
                    "status": "pass",
                    "http_status": 200,
                    "json_ok": True,
                    "trace_id": secret_value,
                    "debug_value": bearer_value,
                }
            },
            "image_probe_results": {
                "gemini-2.5-flash-image": {
                    "status": "pass",
                    "http_status": 200,
                    "image_count": 1,
                    "thumbnail": data_uri_value,
                }
            },
        }
    )

    assert result["status"] == "fail"
    assert "sanitized-payload-fields" in result["blocking_check_ids"]
    assert result["summary"]["forbidden_payload_field_count"] == 4
    reason = next(check["reason"] for check in result["checks"] if check["id"] == "sanitized-payload-fields")
    assert "#api_key_like" in reason
    assert "#bearer_token" in reason
    assert "#email_like" in reason
    assert "#data_uri_like" in reason
    assert secret_value not in str(result)
    assert bearer_value not in str(result)
    assert email_value not in str(result)
    assert data_uri_value not in str(result)


def test_gateway_probe_evaluation_redacts_secret_like_model_ids():
    secret_model = "s" + "k-" + ("B" * 24)
    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "model_ids": [secret_model],
            "chat_probe_results": {secret_model: {"status": "pass", "http_status": 200, "json_ok": True}},
        }
    )

    assert result["status"] == "fail"
    assert "sanitized-payload-fields" in result["blocking_check_ids"]
    assert result["model_rows"][0]["model"] == REDACTED_MODEL_ID
    assert secret_model not in str(result)


def test_gateway_probe_evaluation_route_returns_template_and_evaluation():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    template = client.get("/api/v1/aihub/models/gateway-probe-template")
    assert template.status_code == 200
    assert template.json()["data"]["status"] == "ready"
    assert "image_probe_results" in template.json()["data"]["payload_shape"]

    response = client.post(
        "/api/v1/aihub/models/gateway-probe-evaluation",
        json={
            "models_response": {"data": [{"id": "gemini-2.5-flash-lite"}]},
            "chat_probe_results": {"gemini-2.5-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True}},
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["summary"]["observed_model_count"] == 1

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["gateway_probe_evaluation"]["status"] == "pass"
    assert models_payload["gateway_probe_evaluation"]["source"] == "latest_sanitized_manual_probe"
    probe_check = next(
        check for check in models_payload["model_ops_readiness"]["checks"] if check["id"] == "gateway-probe-evaluation"
    )
    assert probe_check["status"] == "pass"


def test_gateway_probe_evaluation_route_stores_minimal_snapshot_for_rejected_payload():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)
    secret_value = "s" + "k-" + ("C" * 24)

    response = client.post(
        "/api/v1/aihub/models/gateway-probe-evaluation",
        json={
            "models_response": {"data": [{"id": "gemini-2.5-flash-lite"}]},
            "chat_probe_results": {
                "gemini-2.5-flash-lite": {
                    "status": "pass",
                    "http_status": 200,
                    "json_ok": True,
                    "trace_id": secret_value,
                }
            },
        },
    )
    assert response.status_code == 200
    assert secret_value not in str(response.json())

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert secret_value not in str(models_payload)
    assert models_payload["gateway_probe_evaluation"]["status"] == "fail"
    assert models_payload["gateway_probe_evaluation"]["model_rows"] == []
    assert models_payload["gateway_probe_evaluation"]["recommended_env"] == []
    assert "sanitized-payload-fields" in models_payload["gateway_probe_evaluation"]["blocking_check_ids"]


def test_gateway_probe_evaluation_uses_current_defaults_for_change_detection(monkeypatch):
    monkeypatch.setattr(model_gateway_probe_evaluation, "task_default_model", lambda task: "gemini-2.5-flash")

    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {"data": [{"id": "gemini-2.5-flash-lite"}]},
            "chat_probe_results": {"gemini-2.5-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True}},
        }
    )

    assert any(row["requires_change"] for row in result["recommended_env"])


class _FakeModelRow:
    def __init__(self, model_id: str) -> None:
        self.id = model_id


class _FakeModels:
    def __init__(self) -> None:
        self.calls = 0

    async def list(self):
        self.calls += 1
        return type(
            "FakeModelList",
            (),
            {
                "data": [
                    _FakeModelRow("gemini-2.5-flash-lite"),
                    _FakeModelRow("gemini-2.5-flash"),
                    _FakeModelRow("gemini-2.5-pro"),
                ]
            },
        )()


class _FakeLiveMessage:
    content = '{"ok": true, "task": "gateway_probe"}'


class _FakeLiveChoice:
    message = _FakeLiveMessage()


class _FakeLiveResponse:
    choices = [_FakeLiveChoice()]


class _FakeLiveCompletions:
    def __init__(self) -> None:
        self.calls = []

    async def create(self, **params):
        self.calls.append(params)
        return _FakeLiveResponse()


class _FakeLiveChat:
    def __init__(self) -> None:
        self.completions = _FakeLiveCompletions()


class _FakeLiveClient:
    def __init__(self) -> None:
        self.models = _FakeModels()
        self.chat = _FakeLiveChat()


@pytest.mark.asyncio
async def test_gateway_live_probe_dry_run_does_not_call_gateway():
    result = await ModelGatewayLiveProbeService().run({"models": ["gemini-2.5-flash-lite"]})

    assert result["status"] == "dry_run"
    assert result["summary"]["gateway_called"] is False
    assert result["planned_probes"]["chat_models"] == ["gemini-2.5-flash-lite"]
    assert "sk-" not in str(result)


@pytest.mark.asyncio
async def test_gateway_live_probe_executes_fake_client_and_returns_sanitized_evaluation():
    fake_client = _FakeLiveClient()

    result = await ModelGatewayLiveProbeService().run(
        {"execute": True, "models": ["gemini-2.5-flash-lite"], "max_models": 1},
        client=fake_client,
    )

    assert result["status"] == "pass"
    assert fake_client.models.calls == 1
    assert fake_client.chat.completions.calls[0]["model"] == "gemini-2.5-flash-lite"
    assert fake_client.chat.completions.calls[0]["max_tokens"] == 32
    assert result["summary"]["gateway_called"] is True
    assert result["summary"]["raw_outputs_returned"] is False
    assert result["chat_probe_results"]["gemini-2.5-flash-lite"]["json_ok"] is True
    assert result["evaluation"]["status"] == "pass"
    assert "gateway_probe" not in str(result)
    assert "Bearer " not in str(result)
    assert "sk-" not in str(result)


@pytest.mark.asyncio
async def test_gateway_live_probe_blocks_execute_when_runtime_config_missing(monkeypatch):
    from services import model_gateway_live_probe

    monkeypatch.setattr(model_gateway_live_probe.settings, "app_ai_base_url", None)
    monkeypatch.setattr(model_gateway_live_probe.settings, "app_ai_key", None)

    result = await ModelGatewayLiveProbeService().run({"execute": True})

    assert result["status"] == "blocked"
    assert result["summary"]["gateway_called"] is False
    assert "live-probe-configured" in result["blocking_check_ids"]


def test_gateway_live_probe_route_returns_dry_run_contract():
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.post("/api/v1/aihub/models/gateway-live-probe", json={"models": ["gemini-2.5-flash-lite"]})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "dry_run"
    assert payload["summary"]["gateway_called"] is False
    assert payload["planned_probes"]["chat_models"] == ["gemini-2.5-flash-lite"]
