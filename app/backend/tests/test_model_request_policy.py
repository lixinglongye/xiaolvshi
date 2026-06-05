from services.model_request_policy import generation_request_policy_for_api, resolve_generation_request_policy


def test_request_policy_uses_low_cost_defaults_for_classification_json():
    decision = resolve_generation_request_policy(
        task="classification",
        response_format={"type": "json_object"},
    )

    assert decision.effective_temperature == 0.0
    assert decision.effective_max_tokens == 768
    assert decision.response_format_mode == "json"
    assert decision.cost_mode == "policy-default"
    assert "sk-" not in str(decision.to_api())


def test_request_policy_clamps_expensive_fast_request():
    decision = resolve_generation_request_policy(
        task="fast",
        requested_temperature=1.7,
        requested_max_tokens=12000,
    )

    assert decision.effective_temperature == 0.5
    assert decision.effective_max_tokens == 4096
    assert decision.temperature_adjusted is True
    assert decision.max_tokens_adjusted is True


def test_request_policy_preserves_large_review_budget_within_ceiling():
    decision = resolve_generation_request_policy(
        task="review",
        requested_temperature=0.35,
        requested_max_tokens=9000,
    )

    assert decision.effective_temperature == 0.35
    assert decision.effective_max_tokens == 9000
    assert decision.max_tokens_adjusted is False
    assert decision.cost_mode == "caller-expanded"


def test_request_policy_lowers_json_temperature_ceiling_for_review():
    decision = resolve_generation_request_policy(
        task="review",
        requested_temperature=0.6,
        requested_max_tokens=4096,
        response_format={"type": "json_object"},
    )

    assert decision.effective_temperature == 0.2
    assert decision.temperature_adjusted is True
    assert decision.response_format_mode == "json"


def test_request_policy_has_specialized_agentic_and_grounded_defaults():
    agentic = resolve_generation_request_policy(task="agentic-routing", requested_temperature=0.8, requested_max_tokens=6000)
    grounded = resolve_generation_request_policy(task="grounded_research", response_format={"type": "json_object"})

    assert agentic.task == "agentic"
    assert agentic.effective_temperature == 0.4
    assert agentic.effective_max_tokens == 4096
    assert agentic.temperature_adjusted is True
    assert agentic.max_tokens_adjusted is True
    assert grounded.task == "grounded-research"
    assert grounded.effective_temperature == 0.1
    assert grounded.effective_max_tokens == 4096
    assert grounded.response_format_mode == "json"


def test_generation_request_policy_for_api_is_safe():
    payload = generation_request_policy_for_api()

    assert payload["status"] == "ready"
    assert len(payload["task_defaults"]) >= 5
    assert any(item["task"] == "classification" for item in payload["task_policies"])
    assert any(item["task"] == "agentic" for item in payload["task_policies"])
    assert any(item["task"] == "grounded-research" for item in payload["task_policies"])
    assert "sk-" not in str(payload)


def test_model_ops_route_includes_request_policy():
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
    assert payload["request_policy"]["status"] == "ready"
    assert payload["request_policy"]["task_defaults"]
