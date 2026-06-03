from services.model_fallback_chains import ModelFallbackChainService


def test_fallback_chains_build_passes_for_default_policy():
    chains = ModelFallbackChainService().build_chains()

    assert chains["status"] == "pass"
    assert chains["summary"]["chain_count"] >= 7
    assert chains["summary"]["cheap_primary_count"] >= 5
    assert chains["summary"]["fail_count"] == 0
    assert "sk-" not in str(chains)


def test_fallback_chain_starts_fast_and_ocr_on_flash_lite():
    chains = ModelFallbackChainService().build_chains()
    by_task = {chain["task"]: chain for chain in chains["chains"]}

    fast_primary = by_task["fast"]["steps"][0]
    ocr_primary = by_task["ocr"]["steps"][0]

    assert fast_primary["role"] == "primary"
    assert fast_primary["resolved_model"] == "gemini-2.5-flash-lite"
    assert fast_primary["cost_tier"] == "lowest"
    assert ocr_primary["resolved_model"] == "gemini-2.5-flash-lite"
    assert ocr_primary["cost_tier"] == "lowest"


def test_fallback_chain_requires_operator_review_for_review_premium_step():
    chains = ModelFallbackChainService().build_chains()
    review = next(chain for chain in chains["chains"] if chain["task"] == "review")
    premium_steps = [step for step in review["steps"] if step["cost_tier"] == "premium"]

    assert premium_steps
    assert all(step["requires_operator_review"] for step in premium_steps)
    assert review["status"] == "pass"


def test_fallback_chain_allows_pdf_premium_exception_as_primary():
    chains = ModelFallbackChainService().build_chains()
    pdf = next(chain for chain in chains["chains"] if chain["task"] == "pdf")
    primary = pdf["steps"][0]

    assert primary["resolved_model"] == "gemini-2.5-pro"
    assert primary["cost_tier"] == "premium"
    assert primary["requires_operator_review"] is False
    assert pdf["status"] == "pass"


def test_fallback_chain_supports_agentic_gemini_flash_lite_candidate():
    chains = ModelFallbackChainService().build_chains()
    agentic = next(chain for chain in chains["chains"] if chain["task"] == "agentic")
    primary = agentic["steps"][0]

    assert primary["resolved_model"] == "gemini-3.1-flash-lite"
    assert primary["cost_tier"] == "low"
    assert primary["source"] == "capability_matrix"
    assert agentic["status"] == "pass"


def test_model_ops_route_includes_fallback_chains():
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
    assert payload["fallback_chains"]["status"] == "pass"
    assert payload["fallback_chains"]["summary"]["fail_count"] == 0
