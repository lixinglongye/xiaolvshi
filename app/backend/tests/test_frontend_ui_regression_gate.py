import re

from services.frontend_ui_regression_gate import FrontendUiRegressionGateService


def test_frontend_ui_regression_gate_detects_current_frontend_scripts():
    gate = FrontendUiRegressionGateService().build_gate()

    assert gate["status"] == "ready_with_gaps"
    assert gate["summary"]["page_count"] == 4
    assert gate["summary"]["ready_command_gate_count"] == gate["summary"]["required_command_gate_count"]
    command_ids = {row["id"] for row in gate["command_gates"]}
    assert {"frontend-lint", "frontend-typecheck", "frontend-build", "frontend-ui-regression"}.issubset(command_ids)
    assert all(row["script_present"] for row in gate["command_gates"])
    assert "npm run lint" in gate["validation_commands"]
    assert "npm run ui:regression" in gate["validation_commands"]


def test_frontend_ui_regression_gate_maps_maintenance_and_model_ops_pages():
    gate = FrontendUiRegressionGateService().build_gate()
    rows = {row["route"]: row for row in gate["page_rows"]}

    assert set(rows) == {"/maintenance", "/model-ops", "/settings", "/deep-report/:id"}
    assert rows["/maintenance"]["source_exists"] is True
    assert rows["/model-ops"]["source_exists"] is True
    assert rows["/settings"]["source_exists"] is True
    assert rows["/deep-report/:id"]["source_exists"] is True
    assert "user need benchmark coverage" in rows["/maintenance"]["protected_panels"]
    assert "public benchmark license gate" in rows["/maintenance"]["protected_panels"]
    assert "legal benchmark fixture crosswalk" in rows["/maintenance"]["protected_panels"]
    assert "legal benchmark research refresh" in rows["/maintenance"]["protected_panels"]
    assert "model route legal benchmark risk queue" in rows["/maintenance"]["protected_panels"]
    assert "legal RAG authority citation gate" in rows["/maintenance"]["protected_panels"]
    assert "legal RAG hallucination triage gate" in rows["/maintenance"]["protected_panels"]
    assert "legal RAG abstention escalation gate" in rows["/maintenance"]["protected_panels"]
    assert "legal RAG retrieval diagnostics gate" in rows["/maintenance"]["protected_panels"]
    assert "cheap-first calibration" in rows["/model-ops"]["protected_panels"]
    assert "Gemini variant matrix" in rows["/model-ops"]["protected_panels"]
    assert "ModelOps load guard" in rows["/model-ops"]["protected_panels"]
    assert "Performance observations" in rows["/model-ops"]["protected_panels"]
    assert "Gemini catalog source audit" in rows["/model-ops"]["protected_panels"]
    assert "Observed Gemini model intake queue" in rows["/model-ops"]["protected_panels"]
    assert "Observed Gemini coverage gap queue" in rows["/model-ops"]["protected_panels"]
    assert "Model catalog candidate patch plan" in rows["/model-ops"]["protected_panels"]
    assert "Model catalog candidate impact replay" in rows["/model-ops"]["protected_panels"]
    assert "Gemini/NewAPI alias capability coverage" in rows["/model-ops"]["protected_panels"]
    assert "Gateway request compatibility gate" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first release decision" in rows["/model-ops"]["protected_panels"]
    assert "Default change queue" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first priority queue" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first canary plan" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first canary observation review" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first canary promotion decision" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first canary approval packet" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first canary rollback drill" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first canary change manifest" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first maintainer execution checklist" in rows["/model-ops"]["protected_panels"]
    assert "Gemini cheap-first coverage gate" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first quality budget" in rows["/model-ops"]["protected_panels"]
    assert "Model failure upgrade budget" in rows["/model-ops"]["protected_panels"]
    assert "Legal micro benchmark preflight" in rows["/model-ops"]["protected_panels"]
    assert "ModelOps legal benchmark risk bridge" in rows["/model-ops"]["protected_panels"]
    assert "Cheap-first escalation budget" in rows["/model-ops"]["protected_panels"]
    assert "route telemetry repository" in rows["/model-ops"]["protected_panels"]
    assert "route telemetry ops summary" in rows["/model-ops"]["protected_panels"]
    assert "route telemetry triage queue" in rows["/model-ops"]["protected_panels"]
    assert "product feedback capture form" in rows["/settings"]["protected_panels"]
    assert "feedback capture-plan preview" in rows["/settings"]["protected_panels"]
    assert "metadata-only feedback privacy boundary" in rows["/settings"]["protected_panels"]
    assert "report feedback capture form" in rows["/deep-report/:id"]["protected_panels"]
    assert "report id feedback linkage" in rows["/deep-report/:id"]["protected_panels"]
    assert rows["/maintenance"]["status"] == "ready_with_gaps"
    assert rows["/model-ops"]["status"] == "ready_with_gaps"
    assert rows["/settings"]["status"] == "ready_with_gaps"
    assert rows["/deep-report/:id"]["status"] == "ready_with_gaps"
    assert gate["summary"]["missing_page_automation_count"] == 4
    assert "frontend-ui-regression" in rows["/maintenance"]["ready_cover"]
    assert "frontend-ui-regression" in rows["/model-ops"]["ready_cover"]
    assert "frontend-ui-regression" in rows["/settings"]["ready_cover"]
    assert "frontend-ui-regression" in rows["/deep-report/:id"]["ready_cover"]


def test_frontend_ui_regression_gate_is_metadata_only():
    gate = FrontendUiRegressionGateService().build_gate()
    payload_text = str(gate)

    assert gate["privacy_boundary"]["returns_source_code"] is False
    assert gate["privacy_boundary"]["returns_raw_browser_storage"] is False
    assert gate["privacy_boundary"]["returns_raw_prompts"] is False
    assert gate["privacy_boundary"]["returns_raw_payloads"] is False
    assert gate["privacy_boundary"]["returns_raw_query"] is False
    assert gate["privacy_boundary"]["returns_raw_retrieved_context"] is False
    assert gate["privacy_boundary"]["returns_raw_model_output"] is False
    assert gate["privacy_boundary"]["returns_external_legal_text"] is False
    assert gate["privacy_boundary"]["downloads_benchmark_datasets"] is False
    assert gate["privacy_boundary"]["calls_models"] is False
    assert gate["privacy_boundary"]["calls_newapi"] is False
    assert gate["privacy_boundary"]["calls_gemini"] is False
    assert gate["privacy_boundary"]["calls_openai"] is False
    assert gate["privacy_boundary"]["calls_google"] is False
    assert gate["privacy_boundary"]["calls_gateways"] is False
    assert gate["privacy_boundary"]["calls_network"] is False
    assert gate["privacy_boundary"]["writes_model_routes"] is False
    assert gate["privacy_boundary"]["returns_gateway_payloads"] is False
    assert gate["privacy_boundary"]["returns_credentials"] is False
    assert "no datasets" in payload_text
    assert "public scores" in payload_text
    assert "external legal text" in payload_text
    assert "model calls" in payload_text
    assert "gateway calls" in payload_text
    assert "routing writes" in payload_text
    assert "NewAPI/Gemini/gateway calls" in payload_text
    assert "retrieved snippets" in payload_text
    assert "model/gateway/network calls" in payload_text
    assert "fixture questions" in payload_text
    assert "dangerous answers" in payload_text
    assert "raw query" in payload_text
    assert "raw retrieved context" in payload_text
    assert "raw prompts" in payload_text
    assert "payloads" in payload_text
    assert "prompts" in payload_text
    assert "model output" in payload_text
    assert "NewAPI/Gemini/OpenAI/Google/gateway/network calls" in payload_text
    assert "ModelOps observed Gemini coverage gap queue UI evidence is metadata only" in payload_text
    assert "ModelOps Gemini/NewAPI alias capability coverage UI evidence is metadata only" in payload_text
    assert "ModelOps gateway request compatibility gate UI evidence is metadata only" in payload_text
    assert "request bodies" in payload_text
    assert "response bodies" in payload_text
    assert "headers" in payload_text
    assert "ModelOps maintainer execution checklist UI evidence is metadata only" in payload_text
    assert "ModelOps catalog candidate impact replay UI evidence is metadata only" in payload_text
    assert "ModelOps cheap-first escalation budget UI evidence is metadata only" in payload_text
    assert "ModelOps route telemetry UI evidence is metadata only" in payload_text
    assert "sanitized route counters" in payload_text
    assert "Model failure upgrade budget UI evidence is metadata only" in payload_text
    assert "ModelOps legal micro benchmark preflight UI evidence is metadata only" in payload_text
    assert "ModelOps legal benchmark risk bridge UI evidence is metadata only" in payload_text
    assert "Public benchmark license gate UI evidence is metadata only" in payload_text
    assert "public-benchmark-license-gate-regresses" in payload_text
    assert "public benchmark sample text" in payload_text
    assert "public score claims" in payload_text
    assert "modelops-legal-benchmark-risk-bridge-regresses" in payload_text
    assert "modelops-legal-micro-benchmark-preflight-regresses" in payload_text
    assert "gateway-request-compatibility-gate-regresses" in payload_text
    assert "JSON response shapes" in payload_text
    assert "forbidden raw request fields" in payload_text
    assert "route-telemetry-ui-contract-regresses" in payload_text
    assert "remediation env suggestions" in payload_text
    assert "forbidden raw request/model fields" in payload_text
    assert "user-need gaps" in payload_text
    assert "runaway retries" in payload_text
    assert "premium review coverage" in payload_text
    assert "attempt exhaustion" in payload_text
    assert "hard-stop signals" in payload_text
    assert "Legal benchmark fixture crosswalk UI evidence is metadata only" in payload_text
    assert "gemini-cheap-first-coverage-gate-regresses" in payload_text
    assert "gemini-alias-capability-coverage-regresses" in payload_text
    assert "feedback-capture-plan-regresses" in payload_text
    assert "deep-report-feedback-capture-regresses" in payload_text
    assert "raw feedback text" in payload_text
    assert "credentials" in payload_text
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
    assert payload["data"]["summary"]["page_count"] == 4
    assert payload["data"]["status"] == "ready_with_gaps"
