import json
import re

from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def _passing_observations() -> dict[str, dict]:
    template = LegalReviewBenchmarkService().build_fixture_smoke_template()
    return {
        fixture["id"]: {
            "route": fixture["expected_routes"][0],
            "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
        }
        for fixture in template["fixtures"]
    }


def test_legal_fixture_cheap_first_gate_is_not_run_and_metadata_only_by_default():
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate()
    serialized = json.dumps(gate, ensure_ascii=False)

    assert gate["status"] == "not_run"
    assert gate["summary"]["selected_fixture_count"] == 3
    assert gate["summary"]["not_run_count"] == 3
    assert gate["summary"]["raw_fixture_text_returned"] is False
    assert gate["summary"]["raw_model_output_returned"] is False
    assert gate["summary"]["newapi_called"] is False
    assert gate["routing_policy"]["gateway_call_allowed"] is False
    assert all(row["gate_status"] == "not_run" for row in gate["gate_rows"])
    assert all(row["raw_fixture_text_returned"] is False for row in gate["gate_rows"])
    assert "input_excerpt" not in serialized
    assert "output_text" not in serialized
    assert "货款32000元" not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_legal_fixture_cheap_first_gate_allows_passing_cheap_first_fixture_evidence():
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(
        {
            "observations": _passing_observations(),
            "run_metadata": {
                "fixture-service-agreement-small": {
                    "phase": "cheap_first",
                    "model": "gemini-2.5-flash-lite",
                    "estimated_cost_usd": 0.00009,
                }
            },
        }
    )

    assert gate["status"] == "ready"
    assert gate["summary"]["evaluated_fixture_count"] == 3
    assert gate["summary"]["pass_count"] == 3
    assert gate["summary"]["default_evidence_allowed_count"] == 3
    assert gate["summary"]["raw_input_field_count"] >= 1
    assert gate["default_evidence_fixture_ids"] == [
        "fixture-service-agreement-small",
        "fixture-lease-dispute-notice-small",
        "fixture-low-text-pdf-page-small",
    ]
    assert all(row["default_change_evidence_allowed"] is True for row in gate["gate_rows"])
    assert all("known-low-cost-gemini-cheap-first" in row["reason_codes"] for row in gate["gate_rows"])


def test_legal_fixture_cheap_first_gate_blocks_failed_selected_fixture():
    gate = ModelOpsLegalFixtureCheapFirstBenchmarkGateService().build_gate(
        {
            "observations": {
                "fixture-service-agreement-small": {
                    "route": "fast",
                    "output_text": "risk_matrix",
                }
            }
        }
    )
    rows = {row["fixture_id"]: row for row in gate["gate_rows"]}

    assert gate["status"] == "blocked"
    assert gate["summary"]["blocked_count"] == 1
    assert "fixture-service-agreement-small" in gate["blocking_fixture_ids"]
    assert rows["fixture-service-agreement-small"]["gate_status"] == "blocked"
    assert "high-priority-fixture-improvement" in rows["fixture-service-agreement-small"]["reason_codes"]
    assert rows["fixture-service-agreement-small"]["release_action"] == "block_default_change_until_selected_fixture_is_fixed"
    assert rows["fixture-lease-dispute-notice-small"]["gate_status"] == "not_run"


def test_legal_fixture_cheap_first_gate_route_returns_template_and_review():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["status"] == "not_run"
    assert get_payload["data"]["privacy_boundary"]["returns_raw_fixture_text"] is False

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/cheap-first-benchmark-gate",
        json={"observations": _passing_observations()},
    )
    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["data"]["status"] == "ready"
    assert post_payload["data"]["summary"]["default_evidence_allowed_count"] == 3
