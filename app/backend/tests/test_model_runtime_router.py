from services.model_runtime_router import resolve_runtime_model, runtime_router_policy_for_api


def test_runtime_router_uses_review_default_when_task_declared():
    route = resolve_runtime_model(None, task="review")

    assert route.task == "review"
    assert route.resolved_model == "gemini-2.5-flash"
    assert route.budget_mode == "balanced"
    assert route.routed_to_recommended_model is False


def test_runtime_router_downgrades_fast_premium_without_explicit_allowance():
    route = resolve_runtime_model("gemini-2.5-pro", task="fast")

    assert route.task == "fast"
    assert route.requested_resolved_model == "gemini-2.5-pro"
    assert route.resolved_model == "gemini-2.5-flash-lite"
    assert route.is_over_budget is True
    assert route.requires_operator_review is True
    assert route.routed_to_recommended_model is True


def test_runtime_router_allows_over_budget_model_when_explicit():
    route = resolve_runtime_model("gemini-2.5-pro", task="fast", allow_over_budget_model=True)

    assert route.resolved_model == "gemini-2.5-pro"
    assert route.allow_over_budget_model is True
    assert route.routed_to_recommended_model is False
    assert "allowed explicitly" in route.reason


def test_runtime_router_passes_through_unknown_gateway_model_with_warning():
    route = resolve_runtime_model("gateway-private-gemini", task="classification")

    assert route.resolved_model == "gateway-private-gemini"
    assert route.is_known_model is False
    assert route.routed_to_recommended_model is False
    assert "unverified" in route.reason
    assert "sk-" not in str(route.to_api())


def test_runtime_router_uses_image_default_for_auto_image_task():
    route = resolve_runtime_model("auto", task="image")

    assert route.task == "image"
    assert route.requested_resolved_model == "gemini-2.5-flash-image"
    assert route.resolved_model == "gemini-2.5-flash-image"
    assert route.budget_mode == "explicit-media"
    assert route.cost_tier == "low"
    assert route.is_known_model is True
    assert route.routed_to_recommended_model is False


def test_runtime_router_policy_lists_task_defaults_without_secrets():
    policy = runtime_router_policy_for_api()

    assert policy["status"] == "ready"
    assert "task" in policy["request_fields"]
    assert policy["auto_task_inference"]["default_task"] == "auto"
    assert {item["task"] for item in policy["task_defaults"]} >= {"fast", "classification", "review", "pdf", "image"}
    image_default = next(item for item in policy["task_defaults"] if item["task"] == "image")
    assert image_default["resolved_model"] == "gemini-2.5-flash-image"
    assert "sk-" not in str(policy)
