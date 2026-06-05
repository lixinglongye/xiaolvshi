import re

from services.frontend_ui_regression_gate import FrontendUiRegressionGateService


def test_frontend_ui_regression_gate_detects_current_frontend_scripts():
    gate = FrontendUiRegressionGateService().build_gate()

    assert gate["status"] == "ready_with_gaps"
    assert gate["summary"]["page_count"] == 2
    assert gate["summary"]["ready_command_gate_count"] == gate["summary"]["required_command_gate_count"]
    command_ids = {row["id"] for row in gate["command_gates"]}
    assert {"frontend-lint", "frontend-typecheck", "frontend-build", "frontend-ui-regression"}.issubset(command_ids)
    assert all(row["script_present"] for row in gate["command_gates"])
    assert "npm run lint" in gate["validation_commands"]
    assert "npm run ui:regression" in gate["validation_commands"]


def test_frontend_ui_regression_gate_maps_maintenance_and_model_ops_pages():
    gate = FrontendUiRegressionGateService().build_gate()
    rows = {row["route"]: row for row in gate["page_rows"]}

    assert set(rows) == {"/maintenance", "/model-ops"}
    assert rows["/maintenance"]["source_exists"] is True
    assert rows["/model-ops"]["source_exists"] is True
    assert "user need benchmark coverage" in rows["/maintenance"]["protected_panels"]
    assert "cheap-first calibration" in rows["/model-ops"]["protected_panels"]
    assert "ModelOps load guard" in rows["/model-ops"]["protected_panels"]
    assert "Performance observations" in rows["/model-ops"]["protected_panels"]
    assert "Gemini catalog source audit" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first release decision" in rows["/model-ops"]["protected_panels"]
    assert "Default change queue" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first quality budget" in rows["/model-ops"]["protected_panels"]
    assert rows["/maintenance"]["status"] == "ready_with_gaps"
    assert rows["/model-ops"]["status"] == "ready_with_gaps"
    assert gate["summary"]["missing_page_automation_count"] == 2
    assert "frontend-ui-regression" in rows["/maintenance"]["ready_cover"]
    assert "frontend-ui-regression" in rows["/model-ops"]["ready_cover"]


def test_frontend_ui_regression_gate_is_metadata_only():
    gate = FrontendUiRegressionGateService().build_gate()
    payload_text = str(gate)

    assert gate["privacy_boundary"]["returns_source_code"] is False
    assert gate["privacy_boundary"]["returns_raw_browser_storage"] is False
    assert gate["privacy_boundary"]["returns_raw_model_output"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert "function Inner()" not in payload_text
    assert "localStorage.getItem" not in payload_text
    assert re.search(r"\bsk-[A-Za-z0-9]{20,}\b", payload_text) is None


def test_frontend_ui_regression_gate_route_returns_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/frontend-ui-regression-gate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["page_count"] == 2
    assert payload["data"]["status"] == "ready_with_gaps"
