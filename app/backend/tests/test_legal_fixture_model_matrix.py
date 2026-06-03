from services.legal_fixture_model_matrix import LegalFixtureModelMatrixService


def test_legal_fixture_model_matrix_builds_fixture_ladders():
    matrix = LegalFixtureModelMatrixService().build_matrix()

    assert matrix["status"] == "ready"
    assert matrix["summary"]["fixture_count"] >= 4
    assert matrix["summary"]["cheap_first_candidate_count"] == matrix["summary"]["fixture_count"]
    assert matrix["summary"]["operator_review_candidate_count"] >= 1
    assert "sk-" not in str(matrix)


def test_legal_fixture_model_matrix_starts_with_cheap_candidate():
    matrix = LegalFixtureModelMatrixService().build_matrix()
    service_fixture = next(row for row in matrix["fixtures"] if row["fixture_id"] == "fixture-service-agreement-small")
    first = service_fixture["candidate_ladder"][0]

    assert service_fixture["task"] == "fast"
    assert first["role"] == "cheap_first"
    assert first["model"] == "gemini-2.5-flash-lite"
    assert first["cost_tier"] == "lowest"
    assert first["requires_operator_review"] is False
    assert service_fixture["status"] == "pass"


def test_legal_fixture_model_matrix_bounds_pdf_premium_exception():
    matrix = LegalFixtureModelMatrixService().build_matrix()
    pdf_fixture = next(row for row in matrix["fixtures"] if row["fixture_id"] == "fixture-low-text-pdf-page-small")
    premium_candidates = [item for item in pdf_fixture["candidate_ladder"] if item["cost_tier"] == "premium"]

    assert pdf_fixture["task"] == "pdf"
    assert premium_candidates
    assert all(item["role"] in {"task_recommended", "fallback", "premium_exception", "capability_candidate"} for item in premium_candidates)
    assert all(item["over_fixture_budget"] is False for item in premium_candidates)
    assert pdf_fixture["status"] == "pass"


def test_legal_fixture_model_matrix_route_returns_matrix():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/fixture-model-matrix")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["fixture_count"] >= 4
