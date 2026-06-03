from services import model_gateway_compatibility
from services.model_gateway_compatibility import ModelGatewayCompatibilityService


def test_gateway_compatibility_passes_for_default_gemini_models():
    result = ModelGatewayCompatibilityService().evaluate()

    assert result["status"] == "pass"
    assert result["summary"]["configured_role_count"] >= 8
    assert result["summary"]["known_configured_count"] == result["summary"]["configured_role_count"]
    assert result["summary"]["blocking_count"] == 0
    assert "sk-" not in str(result)


def test_gateway_compatibility_accepts_prefixed_gemini_defaults(monkeypatch):
    monkeypatch.setattr(
        model_gateway_compatibility,
        "cheap_text_model",
        lambda: "google/gemini-2.5-flash-lite",
    )
    monkeypatch.setattr(
        model_gateway_compatibility,
        "task_default_model",
        lambda task: "models/gemini-2.5-flash-lite" if task in {"fast", "ocr", "classification"} else "gemini-2.5-flash",
    )

    result = ModelGatewayCompatibilityService().evaluate()
    cheap = {row["id"]: row for row in result["configured_roles"]}["cheap-model"]

    assert result["status"] == "pass"
    assert cheap["canonical_model"] == "gemini-2.5-flash-lite"
    assert cheap["is_gateway_prefixed"] is True


def test_gateway_compatibility_warns_for_unknown_gemini_default(monkeypatch):
    monkeypatch.setattr(model_gateway_compatibility, "cheap_text_model", lambda: "gemini-9-flash-lite")

    result = ModelGatewayCompatibilityService().evaluate()
    cheap = {row["id"]: row for row in result["configured_roles"]}["cheap-model"]

    assert result["status"] == "warn"
    assert cheap["status"] == "warn"
    assert cheap["is_gemini_like"] is True
    assert cheap["is_known_model"] is False


def test_gateway_compatibility_fails_for_non_gemini_default(monkeypatch):
    monkeypatch.setattr(model_gateway_compatibility, "cheap_text_model", lambda: "provider-cheap-model")

    result = ModelGatewayCompatibilityService().evaluate()
    cheap = {row["id"]: row for row in result["configured_roles"]}["cheap-model"]

    assert result["status"] == "fail"
    assert cheap["status"] == "fail"
    assert cheap["is_gemini_like"] is False


def test_model_ops_route_includes_gateway_compatibility():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/aihub/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["gateway_compatibility"]["status"] in {"pass", "warn", "fail"}
    assert payload["gateway_compatibility"]["gateway_examples"]
