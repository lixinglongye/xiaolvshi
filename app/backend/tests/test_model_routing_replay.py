from services.model_routing_replay import ModelRoutingReplayService


def test_routing_replay_passes_default_cheap_first_scenarios():
    replay = ModelRoutingReplayService().run_replay()

    assert replay["status"] == "pass"
    assert replay["summary"]["scenario_count"] >= 8
    assert replay["summary"]["failed_count"] == 0
    assert replay["summary"]["cheap_start_count"] >= 2
    assert "sk-" not in str(replay)


def test_routing_replay_keeps_fast_clean_route_on_flash_lite():
    replay = ModelRoutingReplayService().run_replay()
    scenarios = {item["id"]: item for item in replay["scenarios"]}
    scenario = scenarios["fast-clean-starts-cheap"]

    assert scenario["status"] == "pass"
    assert scenario["actual"]["decision"] == "continue"
    assert scenario["actual"]["resolved_model"] == "gemini-2.5-flash-lite"
    assert scenario["actual"]["cost_tier"] == "lowest"
    assert scenario["actual"]["requires_operator_review"] is False


def test_routing_replay_requires_operator_review_for_premium_review_escalation():
    replay = ModelRoutingReplayService().run_replay()
    scenarios = {item["id"]: item for item in replay["scenarios"]}
    scenario = scenarios["review-citation-failure-premium-reviewed"]

    assert scenario["status"] == "pass"
    assert scenario["actual"]["decision"] == "escalate"
    assert scenario["actual"]["resolved_model"] == "gemini-2.5-pro"
    assert scenario["actual"]["cost_tier"] == "premium"
    assert scenario["actual"]["requires_operator_review"] is True


def test_routing_replay_hard_stops_privacy_without_model_spend():
    replay = ModelRoutingReplayService().run_replay()
    scenarios = {item["id"]: item for item in replay["scenarios"]}
    scenario = scenarios["privacy-hard-stop"]

    assert scenario["status"] == "pass"
    assert scenario["actual"]["decision"] == "stop"
    assert scenario["actual"]["resolved_model"] is None
    assert scenario["actual"]["cost_tier"] == "none"


def test_model_ops_route_includes_routing_replay():
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
    assert payload["routing_replay"]["status"] == "pass"
    assert payload["routing_replay"]["summary"]["failed_count"] == 0
