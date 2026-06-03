from services.model_escalation_policy import ModelEscalationPolicyService


def test_escalation_policy_starts_fast_tasks_on_cheap_model():
    policy = ModelEscalationPolicyService().build_policy()
    plans = {plan["task"]: plan for plan in policy["plans"]}

    fast = plans["fast"]

    assert fast["steps"][0]["model_alias"] == "auto-fast"
    assert fast["steps"][0]["resolved_model"] == "gemini-2.5-flash-lite"
    assert fast["steps"][0]["requires_operator_review"] is False
    assert "fast" in policy["coverage"]["tasks"]
    assert "sk-" not in str(policy)


def test_escalation_policy_escalates_review_failures_to_premium_exception():
    result = ModelEscalationPolicyService().evaluate(
        "review",
        ["citation_audit_fail", "weak_citations"],
    )

    assert result["decision"] == "escalate"
    assert result["next_step"]["model_alias"] == "auto-pdf"
    assert result["next_step"]["resolved_model"] == "gemini-2.5-pro"
    assert result["next_step"]["requires_operator_review"] is True


def test_escalation_policy_allows_pdf_premium_start_without_extra_review():
    policy = ModelEscalationPolicyService().build_policy()
    pdf = next(plan for plan in policy["plans"] if plan["task"] == "pdf")

    assert pdf["steps"][0]["model_alias"] == "auto-pdf"
    assert pdf["steps"][0]["resolved_model"] == "gemini-2.5-pro"
    assert pdf["steps"][0]["requires_operator_review"] is False


def test_escalation_policy_verifies_warning_signals_without_premium_for_fast_task():
    result = ModelEscalationPolicyService().evaluate("fast", ["low_confidence"])

    assert result["decision"] == "verify"
    assert result["next_step"]["model_alias"] == "auto-review"
    assert result["next_step"]["resolved_model"] == "gemini-2.5-flash"
    assert result["next_step"]["requires_operator_review"] is False


def test_escalation_policy_hard_stops_privacy_and_instruction_risk():
    privacy = ModelEscalationPolicyService().evaluate("review", ["privacy_high"])
    instruction = ModelEscalationPolicyService().evaluate("fast", ["instruction_high"])

    assert privacy["decision"] == "stop"
    assert instruction["decision"] == "stop"
    assert privacy["next_step"] is None
    assert instruction["next_step"] is None


def test_model_ops_route_includes_escalation_policy():
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
    assert payload["escalation_policy"]["status"] == "ready"
    assert payload["escalation_policy"]["coverage"]["plan_count"] >= 5
