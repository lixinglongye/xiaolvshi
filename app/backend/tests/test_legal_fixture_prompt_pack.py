from services import legal_fixture_prompt_pack
from services.legal_fixture_prompt_pack import LegalFixturePromptPackService


def test_legal_fixture_prompt_pack_builds_cheap_first_prompts():
    pack = LegalFixturePromptPackService().build_pack()

    assert pack["status"] == "ready"
    assert pack["summary"]["fixture_count"] >= 4
    assert pack["summary"]["priced_prompt_count"] >= 1
    assert pack["summary"]["estimated_total_request_cost_usd"] > 0
    assert pack["prompts"]
    assert {row["fixture_id"] for row in pack["prompts"]} >= {
        "fixture-service-agreement-small",
        "fixture-adversarial-upload-small",
    }
    assert "sk-" not in str(pack)


def test_legal_fixture_prompt_pack_uses_json_schema_and_follow_up_endpoints():
    prompt = LegalFixturePromptPackService().build_pack()["prompts"][0]

    assert prompt["request_parameters"]["response_format"]["type"] == "json_object"
    assert prompt["request_parameters"]["temperature"] <= 0.2
    assert "fixture_id" in prompt["output_schema"]["required"]
    assert "/fixture-smoke" in " ".join(prompt["follow_up_endpoints"])
    assert "/fixture-improvements" in " ".join(prompt["follow_up_endpoints"])


def test_legal_fixture_prompt_pack_prefers_configured_task_model_and_cheapest_trial():
    pack = LegalFixturePromptPackService().build_pack()
    prompts = {row["fixture_id"]: row for row in pack["prompts"]}

    assert prompts["fixture-service-agreement-small"]["recommended_task"] == "fast"
    assert prompts["fixture-service-agreement-small"]["recommended_model"]
    assert prompts["fixture-service-agreement-small"]["cheap_trial_model"]
    assert prompts["fixture-low-text-pdf-page-small"]["recommended_task"] == "pdf"
    assert prompts["fixture-low-text-pdf-page-small"]["completion_tokens_budget"] >= 900


def test_legal_fixture_prompt_pack_warns_for_unknown_model(monkeypatch):
    monkeypatch.setattr(legal_fixture_prompt_pack, "task_default_model", lambda task: "gateway/custom-model")

    pack = LegalFixturePromptPackService().build_pack()

    assert pack["status"] == "warn"
    assert pack["summary"]["unknown_model_count"] == pack["summary"]["fixture_count"]
    assert pack["warning_fixture_ids"]


def test_legal_fixture_prompt_pack_route_returns_pack():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/prompt-pack")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["fixture_count"] >= 4
