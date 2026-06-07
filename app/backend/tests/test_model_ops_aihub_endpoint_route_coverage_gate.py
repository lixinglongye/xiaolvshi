import json
import re

from services.model_ops_aihub_endpoint_route_coverage_gate import (
    ModelOpsAIHubEndpointRouteCoverageGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|authorization|password|secret|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def test_aihub_endpoint_route_coverage_gate_flags_runtime_and_telemetry_gaps():
    gate = ModelOpsAIHubEndpointRouteCoverageGateService().build_gate()
    rows = {row["id"]: row for row in gate["endpoint_rows"]}
    matrix = {row["coverage_key"]: row for row in gate["coverage_matrix"]}

    assert gate["id"] == "modelops-aihub-endpoint-route-coverage-gate"
    assert gate["status"] == "review_required"
    assert gate["summary"]["endpoint_count"] == 7
    assert gate["summary"]["runtime_routed_count"] == 4
    assert gate["summary"]["budget_decision_count"] == 4
    assert gate["summary"]["route_telemetry_count"] == 4
    assert gate["summary"]["usage_recorded_count"] == 7
    assert gate["summary"]["returns_route_payload_count"] == 1
    assert gate["summary"]["legacy_unrouted_count"] == 3
    assert gate["summary"]["model_called"] is False
    assert gate["summary"]["gateway_called"] is False
    assert gate["summary"]["network_called"] is False
    assert gate["summary"]["configuration_written"] is False
    assert gate["summary"]["traffic_shifted"] is False
    assert gate["blocking_check_ids"] == []
    assert "runtime-router-coverage" in gate["warning_check_ids"]
    assert "route-telemetry-coverage" in gate["warning_check_ids"]
    assert "response-route-payload-coverage" in gate["warning_check_ids"]
    assert "legacy-media-budget-route-gap" in gate["warning_check_ids"]

    assert rows["aihub-gentxt"]["route_status"] == "ready"
    assert rows["aihub-gentxt"]["uses_runtime_router"] is True
    assert rows["aihub-gentxt"]["records_route_telemetry"] is True
    assert rows["aihub-gentxt"]["returns_route_payloads"] is True
    assert rows["aihub-gentxt"]["route_gap_reason_codes"] == ["endpoint_route_coverage_ready"]

    assert rows["aihub-gentxt-stream"]["uses_runtime_router"] is True
    assert rows["aihub-gentxt-stream"]["records_route_telemetry"] is True
    assert rows["aihub-gentxt-stream"]["returns_route_payloads"] is False
    assert "stream_metadata_not_returned" in rows["aihub-gentxt-stream"]["route_gap_reason_codes"]

    assert rows["aihub-genimg"]["route_mode"] == "explicit_media_runtime"
    assert rows["aihub-analyzepdf"]["route_mode"] == "premium_exception_runtime"
    assert rows["aihub-genvideo"]["route_mode"] == "legacy_media_unrouted"
    assert rows["aihub-genvideo"]["uses_runtime_router"] is False
    assert rows["aihub-genvideo"]["records_route_telemetry"] is False
    assert "runtime_router_missing" in rows["aihub-genvideo"]["route_gap_reason_codes"]
    assert "budget_task_missing" in rows["aihub-genaudio"]["route_gap_reason_codes"]
    assert "route_telemetry_missing" in rows["aihub-transcribe"]["route_gap_reason_codes"]

    assert matrix["uses_runtime_router"]["covered_endpoint_count"] == 4
    assert "aihub-genvideo" in matrix["uses_runtime_router"]["gap_endpoint_ids"]
    assert "aihub-genaudio" in matrix["records_route_telemetry"]["gap_endpoint_ids"]
    assert "aihub-transcribe" in matrix["returns_route_payloads"]["gap_endpoint_ids"]


def test_aihub_endpoint_route_coverage_gate_boundaries_are_metadata_only():
    gate = ModelOpsAIHubEndpointRouteCoverageGateService().build_gate(
        {
            "endpoint_rows": [
                {
                    "id": "client@example.com",
                    "raw_prompt": "sk-THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED_123456789",
                }
            ]
        }
    )
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["privacy_boundary"]["metadata_only"] is True
    assert gate["privacy_boundary"]["model_called"] is False
    assert gate["privacy_boundary"]["gateway_called"] is False
    assert gate["privacy_boundary"]["network_called"] is False
    assert gate["privacy_boundary"]["configuration_written"] is False
    assert gate["privacy_boundary"]["traffic_shifted"] is False
    assert gate["privacy_boundary"]["returns_request_body"] is False
    assert gate["privacy_boundary"]["returns_response_body"] is False
    assert gate["claim_boundary"]["runtime_route_migration_completed"] is False
    assert gate["claim_boundary"]["legacy_media_routes_fixed"] is False
    assert gate["claim_boundary"]["automatic_default_change_claimed"] is False
    assert gate["claim_boundary"]["claims_default_route_changed"] is False
    assert "THIS_SHOULD_NOT_BE_ACCEPTED_OR_ECHOED" not in serialized
    assert "client@example.com" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_aihub_endpoint_route_coverage_gate_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    response = client.get("/api/v1/aihub/models/aihub-endpoint-route-coverage-gate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "modelops-aihub-endpoint-route-coverage-gate"
    assert payload["data"]["summary"]["endpoint_count"] == 7
    assert payload["data"]["summary"]["gateway_called"] is False

    posted = client.post(
        "/api/v1/aihub/models/aihub-endpoint-route-coverage-gate",
        json={"raw_prompt": "do not echo", "model": "sk-THIS_SHOULD_NOT_BE_ECHOED_123456789"},
    )
    assert posted.status_code == 200
    assert posted.json()["data"]["summary"]["endpoint_count"] == 7
    assert "THIS_SHOULD_NOT_BE_ECHOED" not in json.dumps(posted.json(), ensure_ascii=False)

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert (
        models_payload["aihub_endpoint_route_coverage_gate"]["id"]
        == "modelops-aihub-endpoint-route-coverage-gate"
    )
    assert any(
        check["source_key"] == "aihub_endpoint_route_coverage_gate"
        for check in models_payload["model_ops_readiness"]["checks"]
    )
