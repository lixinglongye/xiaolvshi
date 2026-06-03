from services.model_reasoning_policy import resolve_reasoning_effort, reasoning_policy_for_api


def test_reasoning_policy_disables_thinking_for_flash_lite_fast_tasks():
    decision = resolve_reasoning_effort(
        model="gemini-2.5-flash-lite",
        task="classification",
    )

    assert decision.effective_effort == "none"
    assert decision.gateway_parameter == "none"
    assert decision.cost_mode == "thinking-disabled"
    assert decision.adjusted is False


def test_reasoning_policy_uses_low_for_review_and_high_for_pdf():
    review = resolve_reasoning_effort(model="gemini-2.5-flash", task="review")
    pdf = resolve_reasoning_effort(model="gemini-2.5-pro", task="pdf")

    assert review.effective_effort == "low"
    assert review.gateway_parameter == "low"
    assert pdf.effective_effort == "high"
    assert pdf.gateway_parameter == "high"


def test_reasoning_policy_coerces_unsupported_none_for_pro_models():
    decision = resolve_reasoning_effort(
        model="gemini-2.5-pro",
        task="review",
        requested_effort="none",
    )

    assert decision.effective_effort == "low"
    assert decision.gateway_parameter == "low"
    assert decision.adjusted is True
    assert "not supported" in decision.reason


def test_reasoning_policy_coerces_medium_for_gemini_3_pro_preview():
    decision = resolve_reasoning_effort(
        model="gemini-3.1-pro-preview",
        task="pdf",
        requested_effort="medium",
    )

    assert decision.effective_effort == "low"
    assert decision.gateway_parameter == "low"
    assert decision.supported_efforts == ("low", "high")


def test_reasoning_policy_omits_unknown_gateway_models():
    decision = resolve_reasoning_effort(
        model="gateway-private-gemini",
        task="review",
    )

    assert decision.gateway_parameter is None
    assert decision.cost_mode == "not-applicable"


def test_reasoning_policy_for_api_is_safe():
    payload = reasoning_policy_for_api()

    assert payload["status"] == "ready"
    assert payload["request_field"]["default"] == "auto"
    assert len(payload["task_defaults"]) >= 5
    assert "sk-" not in str(payload)


def test_model_ops_route_includes_reasoning_policy():
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
    assert payload["reasoning_policy"]["status"] == "ready"
    assert payload["reasoning_policy"]["task_defaults"]
