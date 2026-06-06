import json
import re

from services.model_failure_upgrade_budget import ModelFailureUpgradeBudgetService


SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b"
)


def test_failure_upgrade_budget_default_payload_allows_bounded_retry_up():
    result = ModelFailureUpgradeBudgetService().build_decision()

    assert result["status"] == "pass"
    assert result["summary"]["default_payload_used"] is True
    assert result["decision"]["decision"] == "allow_retry_up"
    assert result["decision"]["task"] == "classification"
    assert result["decision"]["next_cost_tier"] in {"low", "lowest"}
    assert result["summary"]["model_called"] is False
    assert result["summary"]["gateway_called"] is False
    assert result["privacy_boundary"]["metadata_only"] is True
    assert result["blocking_check_ids"] == []


def test_failure_upgrade_budget_keeps_timeout_retry_non_premium_for_fast_task():
    result = ModelFailureUpgradeBudgetService().build_decision(
        {
            "task": "fast",
            "attempt_index": 1,
            "failure_signals": ["timeout"],
            "current_model": "auto-fast",
            "prompt_tokens": 1200,
            "completion_tokens": 256,
            "plan_type": "personal",
        }
    )

    assert result["status"] == "pass"
    assert result["decision"]["decision"] == "allow_retry_up"
    assert result["decision"]["next_cost_tier"] == "low"
    assert result["decision"]["requires_operator_review"] is False
    assert result["decision"]["quota_decision"] is None


def test_failure_upgrade_budget_blocks_premium_without_operator_approval():
    result = ModelFailureUpgradeBudgetService().build_decision(
        {
            "task": "review",
            "attempt_index": 1,
            "failure_signals": ["citation_audit_fail"],
            "current_model": "auto-review",
            "prompt_tokens": 22000,
            "completion_tokens": 2048,
            "plan_type": "personal",
            "premium_escalations_used_month": 0,
            "operator_approved": False,
        }
    )

    assert result["status"] == "fail"
    assert result["decision"]["decision"] == "block_premium_upgrade"
    assert result["decision"]["next_cost_tier"] == "premium"
    assert result["decision"]["requires_operator_review"] is True
    assert result["decision"]["quota_decision"]["allowed"] is False
    assert "premium_operator_approval_required" in result["decision"]["quota_decision"]["over_limit_codes"]
    assert "premium-quota-and-approval" in result["blocking_check_ids"]


def test_failure_upgrade_budget_allows_review_premium_with_approval_and_quota():
    result = ModelFailureUpgradeBudgetService().build_decision(
        {
            "task": "review",
            "attempt_index": 1,
            "failure_signals": ["quality_gate_fail"],
            "current_model": "auto-review",
            "prompt_tokens": 22000,
            "completion_tokens": 2048,
            "plan_type": "lawyer",
            "premium_escalations_used_month": 0,
            "operator_approved": True,
        }
    )

    assert result["status"] in {"pass", "review_required"}
    assert result["decision"]["decision"] == "allow_premium_upgrade_after_operator_review"
    assert result["decision"]["quota_decision"]["allowed"] is True
    assert result["claim_boundary"]["premium_call_authorized"] is True
    assert result["claim_boundary"]["retry_executed"] is False


def test_failure_upgrade_budget_does_not_allow_premium_when_cost_blocker_remains():
    result = ModelFailureUpgradeBudgetService().build_decision(
        {
            "task": "review",
            "attempt_index": 1,
            "failure_signals": ["quality_gate_fail"],
            "current_model": "auto-review",
            "prompt_tokens": 250000,
            "completion_tokens": 20000,
            "plan_type": "lawyer",
            "premium_escalations_used_month": 0,
            "operator_approved": True,
        }
    )

    assert result["status"] == "fail"
    assert result["decision"]["decision"] == "block_upgrade"
    assert "incremental-cost" in result["blocking_check_ids"]
    assert result["claim_boundary"]["premium_call_authorized"] is False


def test_failure_upgrade_budget_hard_stop_prevents_retry():
    result = ModelFailureUpgradeBudgetService().build_decision(
        {
            "task": "classification",
            "attempt_index": 0,
            "failure_signals": ["privacy_high"],
            "current_model": "auto-fast",
        }
    )

    assert result["status"] == "fail"
    assert result["decision"]["decision"] == "stop_hard_signal"
    assert "hard-stop-signal" in result["blocking_check_ids"]


def test_failure_upgrade_budget_attempt_exhaustion_blocks_more_retries():
    result = ModelFailureUpgradeBudgetService().build_decision(
        {
            "task": "classification",
            "attempt_index": 2,
            "failure_signals": ["schema_missing_required"],
            "current_model": "auto-fast",
        }
    )

    assert result["status"] == "fail"
    assert result["decision"]["decision"] == "stop_attempt_budget_exhausted"
    assert "attempt-budget" in result["blocking_check_ids"]


def test_failure_upgrade_budget_rejects_sensitive_payload_without_echoing_values():
    secret = "s" + "k-" + "b" * 24
    result = ModelFailureUpgradeBudgetService().build_decision(
        {
            "task": "fast",
            "attempt_index": 1,
            "failure_signals": ["timeout"],
            "headers": {"authorization": secret},
            "prompt": "do not echo this prompt",
            "raw_model_output": "client@example.com 13812345678 110101199003071234",
        }
    )
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["status"] == "fail"
    assert result["decision"]["decision"] == "reject_unsanitized_payload"
    assert result["summary"]["forbidden_payload_field_count"] >= 3
    assert result["summary"]["secret_like_value_count"] >= 2
    assert "do not echo this prompt" not in serialized
    assert "client@example.com" not in serialized
    assert "13812345678" not in serialized
    assert secret not in serialized
    assert not SENSITIVE_PATTERN.search(serialized)


def test_failure_upgrade_budget_routes_and_model_ops_payload_include_gate():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.aihub import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/aihub/models/failure-upgrade-budget")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["decision"]["decision"] == "allow_retry_up"

    template_response = client.get("/api/v1/aihub/models/failure-upgrade-budget-template")
    assert template_response.status_code == 200
    assert "prompt" in template_response.json()["data"]["forbidden"]

    post_response = client.post(
        "/api/v1/aihub/models/failure-upgrade-budget",
        json={"task": "classification", "attempt_index": 2, "failure_signals": ["schema_missing_required"]},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["decision"]["decision"] == "stop_attempt_budget_exhausted"

    models_response = client.get("/api/v1/aihub/models")
    assert models_response.status_code == 200
    models_payload = models_response.json()
    assert models_payload["failure_upgrade_budget"]["status"] == "pass"
