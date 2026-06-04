from services import model_gateway_probe_evaluation
from services.model_gateway_probe_evaluation import ModelGatewayProbeEvaluationService


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


def test_gateway_probe_evaluation_route_returns_template_and_evaluation():
    import pytest

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


def test_gateway_probe_evaluation_uses_current_defaults_for_change_detection(monkeypatch):
    monkeypatch.setattr(model_gateway_probe_evaluation, "task_default_model", lambda task: "gemini-2.5-flash")

    result = ModelGatewayProbeEvaluationService().evaluate(
        {
            "models_response": {"data": [{"id": "gemini-2.5-flash-lite"}]},
            "chat_probe_results": {"gemini-2.5-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True}},
        }
    )

    assert any(row["requires_change"] for row in result["recommended_env"])
