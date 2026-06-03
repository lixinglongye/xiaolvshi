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
                ]
            },
            "chat_probe_results": {
                "models/gemini-2.5-flash-lite": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 900},
                "gemini-2.5-flash": {"status": "pass", "http_status": 200, "json_ok": True, "latency_ms": 1200},
            },
        }
    )

    assert result["status"] == "pass"
    assert result["summary"]["cheap_candidate_count"] >= 1
    assert result["summary"]["probed_cheap_candidate_count"] >= 1
    assert {row["env_var"]: row["recommended_value"] for row in result["recommended_env"]}["APP_AI_CHEAP_MODEL"] == "models/gemini-2.5-flash-lite"
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
