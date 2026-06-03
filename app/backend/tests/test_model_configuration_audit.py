from services import model_configuration_audit
from services.model_configuration_audit import ModelConfigurationAuditService


def _reset_default_models(monkeypatch):
    monkeypatch.setattr(model_configuration_audit, "cheap_text_model", lambda: "gemini-2.5-flash-lite")
    monkeypatch.setattr(model_configuration_audit, "balanced_text_model", lambda: "gemini-2.5-flash")
    monkeypatch.setattr(model_configuration_audit, "premium_text_model", lambda: "gemini-2.5-pro")

    def task_default(task: str) -> str:
        return {
            "fast": "gemini-2.5-flash-lite",
            "ocr": "gemini-2.5-flash-lite",
            "classification": "gemini-2.5-flash-lite",
            "review": "gemini-2.5-flash",
            "pdf": "gemini-2.5-pro",
        }.get(task, "gemini-2.5-flash")

    monkeypatch.setattr(model_configuration_audit, "task_default_model", task_default)


def test_model_configuration_audit_passes_default_roles(monkeypatch):
    _reset_default_models(monkeypatch)

    result = ModelConfigurationAuditService().audit()

    assert result["status"] == "pass"
    assert result["blocking_check_ids"] == []
    assert result["summary"]["unknown_model_count"] == 0
    assert "sk-" not in str(result)


def test_model_configuration_audit_fails_when_cheap_role_is_premium(monkeypatch):
    _reset_default_models(monkeypatch)
    monkeypatch.setattr(model_configuration_audit, "cheap_text_model", lambda: "gemini-2.5-pro")

    result = ModelConfigurationAuditService().audit()

    assert result["status"] == "fail"
    assert "cheap-model-role" in result["blocking_check_ids"]
    cheap = next(check for check in result["checks"] if check["id"] == "cheap-model-role")
    assert cheap["over_budget"] is True


def test_model_configuration_audit_warns_on_unknown_gateway_default(monkeypatch):
    _reset_default_models(monkeypatch)
    monkeypatch.setattr(model_configuration_audit, "balanced_text_model", lambda: "newapi-private-balanced")

    result = ModelConfigurationAuditService().audit()

    assert result["status"] == "warn"
    assert "balanced-model-role" in result["warning_check_ids"]
    assert result["summary"]["unknown_model_count"] == 1


def test_model_ops_route_includes_model_configuration_audit():
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
    assert payload["model_configuration_audit"]["status"] in {"pass", "warn", "fail"}
    assert payload["model_configuration_audit"]["checks"]
