import json
import re

from services.model_ops_cheap_first_escalation_budget import ModelOpsCheapFirstEscalationBudgetService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def test_escalation_budget_default_observations_pass_metadata_only():
    budget = ModelOpsCheapFirstEscalationBudgetService().build_budget()
    serialized = json.dumps(budget, ensure_ascii=False)

    assert budget["status"] == "pass"
    assert budget["summary"]["default_observation_used"] is True
    assert budget["summary"]["observation_count"] >= 4
    assert budget["summary"]["total_request_count"] >= 1000
    assert budget["summary"]["escalation_count"] > 0
    assert budget["summary"]["premium_escalation_count"] == budget["summary"]["operator_review_count"]
    assert budget["summary"]["wasted_escalation_cost_ratio"] < 0.25
    assert budget["privacy_boundary"]["metadata_only"] is True
    assert budget["privacy_boundary"]["gateway_called"] is False
    assert budget["privacy_boundary"]["raw_model_output_included"] is False
    assert budget["claim_boundary"]["production_accuracy_claimed"] is False
    assert not SENSITIVE_PATTERN.search(serialized)


def test_escalation_budget_accepts_clean_aggregate_observations():
    budget = ModelOpsCheapFirstEscalationBudgetService().build_budget(
        {
            "observations": [
                {
                    "task": "fast",
                    "phase": "local_fixture",
                    "request_count": 100,
                    "primary_failure_count": 2,
                    "verification_count": 3,
                    "escalation_count": 2,
                    "successful_after_escalation_count": 2,
                    "premium_escalation_count": 0,
                    "operator_review_count": 0,
                    "primary_cost_usd": 0.01,
                    "verification_cost_usd": 0.003,
                    "escalation_cost_usd": 0.004,
                }
            ]
        }
    )
    row = budget["budget_rows"][0]

    assert budget["status"] == "pass"
    assert budget["summary"]["default_observation_used"] is False
    assert row["status"] == "pass"
    assert row["primary_failure_rate"] == 0.02
    assert row["escalation_success_rate"] == 1.0
    assert row["premium_review_coverage"] is True
    assert budget["blocking_check_ids"] == []


def test_escalation_budget_fails_on_runaway_retry_and_premium_without_review():
    budget = ModelOpsCheapFirstEscalationBudgetService().build_budget(
        {
            "observations": [
                {
                    "task": "review",
                    "phase": "bad_cascade",
                    "request_count": 100,
                    "primary_failure_count": 20,
                    "verification_count": 30,
                    "escalation_count": 25,
                    "successful_after_escalation_count": 2,
                    "premium_escalation_count": 8,
                    "operator_review_count": 1,
                    "primary_cost_usd": 0.10,
                    "verification_cost_usd": 0.20,
                    "escalation_cost_usd": 0.60,
                    "premium_cost_usd": 0.50,
                }
            ]
        }
    )
    row = budget["budget_rows"][0]

    assert budget["status"] == "fail"
    assert row["status"] == "fail"
    assert set(row["reason_codes"]) >= {
        "primary-failure-rate",
        "escalation-rate",
        "premium-escalation-rate",
        "wasted-escalation-cost-ratio",
        "escalation-success-rate",
        "premium-operator-review-coverage",
    }
    assert "row-thresholds" in budget["blocking_check_ids"]
    assert "premium-review-coverage" in budget["blocking_check_ids"]
    assert budget["blocking_observation_ids"] == ["escalation-budget-review-bad_cascade"]


def test_escalation_budget_warns_on_low_volume_clean_row():
    budget = ModelOpsCheapFirstEscalationBudgetService().build_budget(
        {
            "observations": [
                {
                    "task": "classification",
                    "phase": "tiny_local_batch",
                    "request_count": 5,
                    "primary_failure_count": 0,
                    "escalation_count": 0,
                    "successful_after_escalation_count": 0,
                    "primary_cost_usd": 0.001,
                }
            ]
        }
    )
    row = budget["budget_rows"][0]

    assert budget["status"] == "review_required"
    assert row["status"] == "warn"
    assert "minimum-request-count" in row["reason_codes"]
    assert "row-thresholds" in budget["warning_check_ids"]


def test_escalation_budget_rejects_sensitive_payload_without_echoing_values():
    secret = "s" + "k-" + "a" * 24
    payload = {
        "observations": [
            {
                "task": "fast",
                "request_count": 100,
                "primary_failure_count": 0,
            }
        ],
        "headers": {"authorization": secret},
        "raw_model_output": "client@example.com 13812345678 110101199003071234",
        "prompt": "do not echo this",
    }

    budget = ModelOpsCheapFirstEscalationBudgetService().build_budget(payload)
    serialized = json.dumps(budget, ensure_ascii=False)

    assert budget["status"] == "fail"
    assert budget["summary"]["forbidden_payload_field_count"] >= 3
    assert budget["summary"]["secret_like_value_count"] >= 2
    assert "do not echo this" not in serialized
    assert "client@example.com" not in serialized
    assert "13812345678" not in serialized
    assert secret not in serialized
    assert budget["privacy_boundary"]["credentials_included"] is False


def test_escalation_budget_routes_and_model_ops_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/cheap-first-escalation-budget")
    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["success"] is True
    assert get_payload["data"]["status"] == "pass"

    post_response = client.post(
        "/api/v1/aihub/models/cheap-first-escalation-budget",
        json={"observations": [{"task": "fast", "request_count": 5}]},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "review_required"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["cheap_first_escalation_budget"]["status"] == "pass"
    assert "cheap_first_escalation_budget" in {
        check["source_key"] for check in models_payload["model_ops_readiness"]["checks"]
    }
    assert any(
        check["source_key"] == "cheap_first_escalation_budget"
        for check in models_payload["cheap_first_release_decision"]["checks"]
    )
