import json
import re

from services.model_ops_legal_benchmark_risk_bridge import ModelOpsLegalBenchmarkRiskBridgeService


SECRET_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN PRIVATE KEY|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


def test_legal_benchmark_risk_bridge_summarizes_route_watchlist():
    bridge = ModelOpsLegalBenchmarkRiskBridgeService().build_bridge()
    rows = {row["task_id"]: row for row in bridge["route_reviews"]}

    assert bridge["id"] == "modelops-legal-benchmark-risk-bridge"
    assert bridge["status"] == "review_required"
    assert bridge["summary"]["route_review_count"] >= 6
    assert bridge["summary"]["blocking_route_count"] == 0
    assert bridge["summary"]["watch_route_count"] >= 1
    assert bridge["summary"]["premium_exception_route_count"] == 1
    assert bridge["bridge_policy"]["current_cheap_first_defaults_allowed"] is True
    assert bridge["bridge_policy"]["new_default_promotion_allowed"] is False
    assert rows["legal-review-balanced"]["balanced_precheck_required"] is True
    assert rows["large-pdf-premium-exception"]["premium_exception_required"] is True
    assert "benchmark-license-review" in rows["legal-review-balanced"]["reason_codes"]


def test_legal_benchmark_risk_bridge_tracks_user_need_evidence():
    bridge = ModelOpsLegalBenchmarkRiskBridgeService().build_bridge()
    need_rows = {row["need_id"]: row for row in bridge["user_need_reviews"]}

    assert "cheap-first-review-routing" in need_rows
    assert "traceable-legal-review" in need_rows
    assert need_rows["traceable-legal-review"]["premium_exception_count"] == 1
    assert need_rows["cheap-first-review-routing"]["cheap_first_allowed_count"] >= 3
    assert all(row["research_source_ids"] for row in need_rows.values())


def test_legal_benchmark_risk_bridge_is_metadata_only():
    bridge = ModelOpsLegalBenchmarkRiskBridgeService().build_bridge()
    serialized = json.dumps(bridge, ensure_ascii=False)

    assert bridge["summary"]["newapi_called"] is False
    assert bridge["summary"]["network_called"] is False
    assert bridge["summary"]["dataset_downloaded"] is False
    assert bridge["summary"]["configuration_written"] is False
    assert bridge["summary"]["traffic_shifted"] is False
    assert bridge["privacy_boundary"]["returns_raw_benchmark_samples"] is False
    assert bridge["privacy_boundary"]["returns_raw_legal_text"] is False
    assert bridge["privacy_boundary"]["returns_raw_model_output"] is False
    assert bridge["privacy_boundary"]["returns_credentials"] is False
    assert bridge["claim_boundary"]["public_benchmark_scores_claimed"] is False
    assert bridge["claim_boundary"]["default_model_changed"] is False
    assert not SECRET_PATTERN.search(serialized)


def test_legal_benchmark_risk_bridge_route_and_model_ops_payload_include_signal():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    route_response = client.get("/api/v1/aihub/models/legal-benchmark-risk-bridge")
    assert route_response.status_code == 200
    route_payload = route_response.json()["data"]
    assert route_payload["status"] == "review_required"
    assert route_payload["summary"]["route_review_count"] >= 6

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["legal_benchmark_risk_bridge"]["id"] == "modelops-legal-benchmark-risk-bridge"
    assert models_payload["legal_benchmark_risk_bridge"]["summary"]["newapi_called"] is False
