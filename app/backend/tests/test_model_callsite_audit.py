from services.model_callsite_audit import ModelCallsiteAuditService


def test_model_callsite_audit_requires_explicit_tasks_for_service_calls():
    audit = ModelCallsiteAuditService().audit()

    assert audit["status"] == "pass"
    assert audit["summary"]["callsite_count"] >= 8
    assert audit["summary"]["missing_task_count"] == 0
    assert audit["summary"]["explicit_task_count"] == audit["summary"]["callsite_count"]
    assert "sk-" not in str(audit)


def test_model_ops_route_includes_callsite_audit():
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
    assert payload["callsite_audit"]["status"] == "pass"
    assert payload["callsite_audit"]["summary"]["missing_task_count"] == 0
