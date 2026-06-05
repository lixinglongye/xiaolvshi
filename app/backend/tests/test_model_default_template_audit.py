import re

from services.model_default_template_audit import ModelDefaultTemplateAuditService


SECRET_PATTERN = re.compile(r"sk-[A-Za-z0-9]{20,}|password|api[_-]?key", re.IGNORECASE)


def test_model_default_template_audit_passes_for_checked_in_defaults():
    audit = ModelDefaultTemplateAuditService().build_audit()
    rows = {row["env_var"]: row for row in audit["rows"]}

    assert audit["status"] == "pass"
    assert audit["summary"]["drift_count"] == 0
    assert audit["summary"]["agentic_grounded_defaults_visible"] is True
    assert rows["APP_AI_AGENTIC_MODEL"]["expected_default"] == "gemini-3.1-flash-lite"
    assert rows["APP_AI_GROUNDED_RESEARCH_MODEL"]["expected_default"] == "gemini-3.1-flash-lite"
    assert rows["APP_AI_AGENTIC_MODEL"]["source_values"]["env_example"] == "gemini-3.1-flash-lite"
    assert rows["APP_AI_AGENTIC_MODEL"]["source_values"]["readme"] == "gemini-3.1-flash-lite"
    assert rows["APP_AI_AGENTIC_MODEL"]["source_values"]["ai_model_strategy"] == "gemini-3.1-flash-lite"
    assert audit["privacy_boundary"]["real_env_read"] is False
    assert audit["privacy_boundary"]["gateway_called"] is False
    assert not SECRET_PATTERN.search(str(audit))


def test_model_default_template_audit_blocks_template_drift_without_reading_real_env():
    audit = ModelDefaultTemplateAuditService().build_audit(
        {
            "env_example": "APP_AI_AGENTIC_MODEL=gemini-2.5-pro\nAPP_AI_GROUNDED_RESEARCH_MODEL=gemini-3.1-flash-lite\n",
        }
    )
    rows = {row["env_var"]: row for row in audit["rows"]}

    assert audit["status"] == "fail"
    assert rows["APP_AI_AGENTIC_MODEL"]["status"] == "fail"
    assert rows["APP_AI_AGENTIC_MODEL"]["mismatched_sources"] == ["env_example"]
    assert "default-template-app_ai_agentic_model" in audit["blocking_check_ids"]
    assert audit["summary"]["mismatched_value_count"] >= 1
    assert audit["privacy_boundary"]["real_env_read"] is False


def test_model_default_template_audit_endpoint_and_models_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/default-template-audit")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "pass"
    assert payload["data"]["summary"]["agentic_grounded_defaults_visible"] is True

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["routing_aliases"]["auto-agentic"] == "gemini-3.1-flash-lite"
    assert models_payload["routing_aliases"]["auto-grounded-research"] == "gemini-3.1-flash-lite"
    assert models_payload["default_template_audit"]["status"] == "pass"
    assert any(
        check["source_key"] == "default_template_audit"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
