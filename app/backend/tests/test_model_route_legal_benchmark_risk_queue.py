import json
import re

from services.model_route_legal_benchmark_risk_queue import ModelRouteLegalBenchmarkRiskQueueService


SECRET_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN PRIVATE KEY|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
NETWORK_COMMAND_PATTERN = re.compile(r"\b(curl|wget|Invoke-WebRequest|iwr)\b", re.IGNORECASE)


def test_risk_queue_joins_cheap_first_calibration_to_legal_benchmark_evidence():
    queue = ModelRouteLegalBenchmarkRiskQueueService().build_queue()
    rows = {row["task_id"]: row for row in queue["queue_rows"]}

    assert queue["status"] == "ready_with_watchlist"
    assert queue["method"]["type"] == "model-route-legal-benchmark-risk-queue"
    assert queue["summary"]["queue_row_count"] >= 6
    assert queue["summary"]["cheap_first_allowed_count"] >= 3
    assert queue["summary"]["balanced_precheck_count"] >= 2
    assert queue["summary"]["premium_exception_count"] == 1
    assert queue["summary"]["block_count"] == 0
    assert rows["fast-intake-preflight"]["cheap_first_allowed"] is True
    assert rows["classification-routing"]["cheap_first_allowed"] is True
    assert rows["legal-review-balanced"]["balanced_precheck_required"] is True
    assert rows["large-pdf-premium-exception"]["premium_exception_required"] is True
    assert "legalbench" in rows["legal-review-balanced"]["research_source_ids"]
    assert "coliee" in rows["large-pdf-premium-exception"]["research_source_ids"]
    assert "benchmark-license-review" in rows["legal-review-balanced"]["reason_codes"]


def test_risk_queue_user_need_rows_track_gaps_and_premium_exceptions():
    queue = ModelRouteLegalBenchmarkRiskQueueService().build_queue()
    need_rows = {row["need_id"]: row for row in queue["user_need_rows"]}

    traceable = need_rows["traceable-legal-review"]
    robust = need_rows["robust-extraction-quality"]
    cheap_first = need_rows["cheap-first-review-routing"]

    assert traceable["highest_risk_level"] == "operator_exception"
    assert traceable["premium_exception_count"] == 1
    assert "large-pdf-premium-exception" in traceable["task_ids"]
    assert robust["premium_exception_count"] == 1
    assert cheap_first["cheap_first_allowed_count"] >= 3
    assert cheap_first["public_benchmark_status"] == "license_review_required"
    assert all(row["research_source_ids"] for row in need_rows.values())


def test_risk_queue_is_metadata_only_and_does_not_change_routing():
    queue = ModelRouteLegalBenchmarkRiskQueueService().build_queue()
    payload_text = json.dumps(queue, ensure_ascii=False)

    assert queue["routing_policy"]["configuration_write_allowed"] is False
    assert queue["routing_policy"]["gateway_call_allowed"] is False
    assert queue["routing_policy"]["traffic_shift_allowed"] is False
    assert queue["summary"]["newapi_called"] is False
    assert queue["summary"]["network_called"] is False
    assert queue["summary"]["dataset_downloaded"] is False
    assert queue["summary"]["public_benchmark_score_claimed"] is False
    assert queue["privacy_boundary"]["returns_public_benchmark_text"] is False
    assert queue["privacy_boundary"]["returns_raw_legal_text"] is False
    assert queue["privacy_boundary"]["returns_raw_model_output"] is False
    assert queue["claim_boundary"]["default_model_changed"] is False
    assert not SECRET_PATTERN.search(payload_text)


def test_risk_queue_validation_commands_are_local_pytest_only():
    queue = ModelRouteLegalBenchmarkRiskQueueService().build_queue()
    commands = queue["validation_commands"]
    commands_text = "\n".join(commands)

    assert "python -m pytest tests/test_model_route_legal_benchmark_risk_queue.py -q" in commands
    assert all(command.startswith("python -m pytest ") for command in commands)
    assert all("http" not in command.lower() for command in commands)
    assert not NETWORK_COMMAND_PATTERN.search(commands_text)
    for row in queue["queue_rows"]:
        assert all(command.startswith("python -m pytest ") for command in row["validation_commands"])
        assert row["newapi_called"] is False
        assert row["network_called"] is False
        assert row["dataset_download_required"] is False
        assert row["public_score_claimed"] is False


def test_risk_queue_route_returns_metadata_only_payload():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/model-route-legal-benchmark-risk-queue")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["queue_row_count"] >= 6
    assert payload["data"]["summary"]["newapi_called"] is False
    assert payload["data"]["routing_policy"]["default_strategy"] == "cheap_first_with_fixture_backed_escalation"
