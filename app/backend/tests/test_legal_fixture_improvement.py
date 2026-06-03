from services.legal_fixture_improvement import LegalFixtureImprovementService
from services.legal_review_benchmark import LegalReviewBenchmarkService


def _complete_observations():
    service = LegalReviewBenchmarkService()
    template = service.build_fixture_smoke_template()
    observations = {}
    for fixture in template["fixtures"]:
        observations[fixture["id"]] = {
            "route": fixture["expected_routes"][0],
            "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
        }
    return observations


def test_legal_fixture_improvement_default_is_not_run():
    plan = LegalFixtureImprovementService().build_plan()

    assert plan["status"] == "not_run"
    assert plan["summary"]["action_count"] == 0
    assert plan["recommended_actions"]
    assert "output_text" in plan["smoke_result"]["template"]["default_observations"]["fixture-service-agreement-small"]


def test_legal_fixture_improvement_ready_when_smoke_passes():
    plan = LegalFixtureImprovementService().build_plan(_complete_observations())

    assert plan["status"] == "ready"
    assert plan["smoke_status"] == "pass"
    assert plan["summary"]["action_count"] == 0
    assert plan["actions"] == []


def test_legal_fixture_improvement_maps_missing_signals_to_prompt_and_schema_actions():
    plan = LegalFixtureImprovementService().build_plan(
        {
            "fixture-service-agreement-small": {
                "route": "review",
                "output_text": "short summary only",
            }
        }
    )
    action_ids = {action["id"] for action in plan["actions"]}

    assert plan["status"] == "needs_improvement"
    assert plan["summary"]["high_priority_action_count"] > 0
    assert "fixture-service-agreement-small:signal:liability_cap" in action_ids
    liability_action = next(action for action in plan["actions"] if action["label"] == "liability_cap")
    assert liability_action["report_section"] == "risk_matrix"
    assert "liability caps" in liability_action["prompt_clause"]
    assert "risk_matrix" in plan["grouped_actions"]
    assert "short summary only" not in str(plan)
    assert "sk-" not in str(plan)


def test_legal_fixture_improvement_route_returns_plan():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/fixture-improvements")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "not_run"

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/fixture-improvements",
        json={
            "fixture-service-agreement-small": {
                "route": "review",
                "output_text": "short summary only",
            }
        },
    )
    assert post_response.status_code == 200
    payload = post_response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["action_count"] > 0
