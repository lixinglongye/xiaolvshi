import pytest

from services import model_gateway_probe_evaluation
from services.model_gateway_probe_evaluation import (
    REDACTED_MODEL_ID,
    ModelGatewayProbeEvaluationService,
    model_gateway_probe_evaluation_registry,
)


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
                    {"id": "gemini-2.5-pro"},
                    {"id": "gemini-2.5-flash-image"},
                ]
            },
            "chat_probe_results": {
                "models/gemini-2.5-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 900},
                "gemini-2.5-flash": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 1200},
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
    assert {row["env_var"]: row["recommended_value"] for row in result["recommended_env"]}["APP_AI_CHEAP_MODEL"] == "models/gemini-2.5-flash-lite"
    assert {row["env_var"]: row["recommended_value"] for row in result["recommended_env"]}["APP_AI_IMAGE_MODEL"] == "gemini-2.5-flash-image"
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
