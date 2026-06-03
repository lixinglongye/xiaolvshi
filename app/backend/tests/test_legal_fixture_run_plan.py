from services.legal_fixture_run_plan import LegalFixtureRunPlanService


def test_legal_fixture_run_plan_builds_serial_cheap_first_batches():
    plan = LegalFixtureRunPlanService().build_plan()

    assert plan["status"] == "ready"
    assert plan["summary"]["fixture_count"] >= 4
    assert plan["summary"]["cheap_first_step_count"] == plan["summary"]["fixture_count"]
    assert plan["summary"]["max_parallel_requests"] == 1
    assert plan["summary"]["estimated_min_cost_usd"] > 0
    assert "sk-" not in str(plan)
    assert all(step["max_parallel_requests"] == 1 for step in plan["steps"])


def test_legal_fixture_run_plan_tracks_escalation_without_running_models():
    plan = LegalFixtureRunPlanService().build_plan()
    escalation_steps = [step for step in plan["steps"] if step["phase"] == "escalation_if_needed"]

    assert plan["summary"]["escalation_step_count"] >= 1
    assert escalation_steps
    assert all("only when" in step["run_condition"] for step in escalation_steps)
    assert any(batch["phase"] == "cheap_first" for batch in plan["batches"])
    assert any(batch["phase"] == "escalation_if_needed" for batch in plan["batches"])
    assert plan["summary"]["estimated_max_cost_usd"] >= plan["summary"]["estimated_min_cost_usd"]


def test_legal_fixture_run_plan_includes_observation_targets_and_required_fields():
    plan = LegalFixtureRunPlanService().build_plan()
    step = next(row for row in plan["steps"] if row["fixture_id"] == "fixture-service-agreement-small")

    assert step["observation_target"].endswith("/fixture-smoke")
    assert step["improvement_target"].endswith("/fixture-improvements")
    assert step["required_response_fields"]
    assert "fixture_id" in step["required_response_fields"]
    assert "{{APP_AI_KEY}}" in step["command_hint"]


def test_legal_fixture_run_plan_route_returns_plan():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/fixture-run-plan")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["cheap_first_step_count"] >= 4
