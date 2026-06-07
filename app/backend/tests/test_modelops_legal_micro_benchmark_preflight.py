import json
import re

from services.modelops_legal_micro_benchmark_preflight import (
    ModelOpsLegalMicroBenchmarkPreflightService,
)


FORBIDDEN_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|authorization|api_key|headers|input_excerpt|"
    r"output_text|raw_response|client_email|phone|identity|\$env:APP_AI_KEY|choices\[0\]",
    re.IGNORECASE,
)


def test_micro_benchmark_preflight_builds_small_serial_gemini_packet():
    packet = ModelOpsLegalMicroBenchmarkPreflightService().build_packet()

    assert packet["id"] == "modelops-legal-micro-benchmark-preflight"
    assert packet["status"] == "ready"
    assert packet["summary"]["fixture_limit"] == 2
    assert packet["summary"]["selected_fixture_count"] == 2
    assert packet["summary"]["document_case_count"] == 2
    assert packet["summary"]["fact_consistency_case_count"] == 1
    assert packet["summary"]["request_file_count"] == 2
    assert packet["summary"]["max_parallel_requests"] == 1
    assert 0 < packet["summary"]["estimated_cheap_first_cost_usd"] < 0.01
    assert packet["summary"]["gateway_called"] is False
    assert packet["summary"]["network_called"] is False
    assert packet["summary"]["configuration_written"] is False
    assert packet["cheap_first_policy"]["primary_models"] == ["gemini-2.5-flash-lite"]
    assert packet["cheap_first_policy"]["escalation_allowed_before_smoke_score"] is False
    assert packet["cheap_first_policy"]["default_change_allowed_from_preflight_alone"] is False
    assert [item["fixture_id"] for item in packet["fixture_run_items"]] == [
        "fixture-service-agreement-small",
        "fixture-lease-dispute-notice-small",
    ]
    assert [item["case_id"] for item in packet["document_check_items"]] == [
        "ldoc-civil-complaint-mini",
        "ldoc-lawyer-letter-mini",
    ]
    assert [item["case_id"] for item in packet["fact_consistency_items"]] == [
        "fact-lease-arrears-mini"
    ]


def test_micro_benchmark_preflight_is_metadata_only_and_has_boundaries():
    packet = ModelOpsLegalMicroBenchmarkPreflightService().build_packet(4, 7, 4)
    serialized = json.dumps(packet, ensure_ascii=False)

    assert packet["privacy_boundary"]["metadata_only"] is True
    assert packet["privacy_boundary"]["returns_request_body"] is False
    assert packet["privacy_boundary"]["returns_messages"] is False
    assert packet["privacy_boundary"]["returns_prompt_text"] is False
    assert packet["privacy_boundary"]["returns_fixture_excerpt"] is False
    assert packet["privacy_boundary"]["returns_document_snippet"] is False
    assert packet["privacy_boundary"]["returns_raw_model_output"] is False
    assert packet["privacy_boundary"]["returns_credentials"] is False
    assert packet["claim_boundary"]["live_gateway_quality_claimed"] is False
    assert packet["claim_boundary"]["automatic_default_change_claimed"] is False
    assert packet["summary"]["selected_fixture_count"] == 4
    assert packet["summary"]["document_case_count"] == 7
    assert packet["summary"]["fact_consistency_case_count"] == 4
    assert not FORBIDDEN_PATTERN.search(serialized)


def test_micro_benchmark_preflight_clamps_limits_and_keeps_follow_up_gates():
    packet = ModelOpsLegalMicroBenchmarkPreflightService().build_packet(99, 99, 99)

    assert packet["summary"]["fixture_limit"] == 4
    assert packet["summary"]["document_case_limit"] == 7
    assert packet["summary"]["fact_case_limit"] == 4
    assert len(packet["checks"]) >= 8
    assert packet["blocking_check_ids"] == []
    assert packet["warning_check_ids"] == []
    assert packet["run_sequence"][1]["max_parallel_requests"] == 1
    assert "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate" in packet["follow_up_endpoints"]
    assert "/api/v1/maintenance/legal-review-benchmark/default-promotion-packet" in packet["follow_up_endpoints"]
    assert "tests/test_modelops_legal_micro_benchmark_preflight.py" in packet["validation_commands"][0]


def test_micro_benchmark_preflight_route_and_models_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router as aihub_router
    from routers.maintenance import router as maintenance_router

    app = fastapi.FastAPI()
    app.include_router(aihub_router)
    app.include_router(maintenance_router)
    client = testclient.TestClient(app)

    direct_response = client.get("/api/v1/aihub/models/legal-micro-benchmark-preflight")
    assert direct_response.status_code == 200
    direct_payload = direct_response.json()
    assert direct_payload["success"] is True
    assert direct_payload["data"]["summary"]["selected_fixture_count"] == 2
    assert direct_payload["data"]["privacy_boundary"]["returns_request_body"] is False

    maintenance_response = client.get("/api/v1/maintenance/legal-review-benchmark/micro-benchmark-preflight")
    assert maintenance_response.status_code == 200
    assert maintenance_response.json()["data"]["summary"]["document_case_count"] == 2

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["legal_micro_benchmark_preflight"]["status"] == "ready"
    assert "legal_micro_benchmark_preflight" in {
        check["source_key"] for check in models_payload["model_ops_readiness"]["checks"]
    }
    assert not FORBIDDEN_PATTERN.search(json.dumps(models_payload["legal_micro_benchmark_preflight"], ensure_ascii=False))
