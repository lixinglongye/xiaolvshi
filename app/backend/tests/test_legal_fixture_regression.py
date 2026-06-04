from services.legal_fixture_regression import LegalFixtureRegressionService
from services.legal_review_benchmark import LegalReviewBenchmarkService


def _passing_observations() -> dict[str, dict]:
    template = LegalReviewBenchmarkService().build_fixture_smoke_template()
    return {
        fixture["id"]: {
            "route": fixture["expected_routes"][0],
            "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
        }
        for fixture in template["fixtures"]
    }


def _passing_metadata(cost: float = 0.0001) -> dict[str, dict]:
    return {
        fixture_id: {
            "phase": "cheap_first",
            "model": "gemini-2.5-flash-lite",
            "estimated_cost_usd": cost,
            "http_status": 200,
        }
        for fixture_id in _passing_observations()
    }


def test_legal_fixture_regression_returns_not_run_template():
    comparison = LegalFixtureRegressionService().build_comparison()

    assert comparison["status"] == "not_run"
    assert comparison["release_decision"] == "run_baseline_and_current_fixture_batches"
    assert comparison["summary"]["baseline_observed_fixture_count"] == 0
    assert comparison["summary"]["current_observed_fixture_count"] == 0
    assert comparison["validation_commands"]
    assert "sk-" not in str(comparison)


def test_legal_fixture_regression_passes_stable_current_run():
    passing = _passing_observations()
    comparison = LegalFixtureRegressionService().build_comparison(
        {
            "baseline": {"observations": passing, "run_metadata": _passing_metadata()},
            "current": {"observations": passing, "run_metadata": _passing_metadata()},
        }
    )

    assert comparison["status"] == "pass"
    assert comparison["release_decision"] == "current_fixture_run_is_stable_or_improved"
    assert comparison["summary"]["regressed_fixture_count"] == 0
    assert comparison["summary"]["compared_fixture_count"] >= 4
    assert comparison["summary"]["score_delta_avg"] == 0


def test_legal_fixture_regression_blocks_new_fixture_failure_without_raw_echo():
    passing = _passing_observations()
    current = dict(passing)
    current["fixture-service-agreement-small"] = {
        "route": "fast",
        "output_text": "risk_matrix private raw model text must not be echoed",
        "raw_response": {"content": "do not store raw response"},
    }

    comparison = LegalFixtureRegressionService().build_comparison(
        {
            "baseline": {"observations": passing},
            "current": {"observations": current},
        }
    )

    assert comparison["status"] == "fail"
    assert comparison["release_decision"] == "block_default_promotion_until_regressions_are_fixed"
    assert "fixture-service-agreement-small" in comparison["regressed_fixture_ids"]
    target = next(row for row in comparison["fixture_deltas"] if row["fixture_id"] == "fixture-service-agreement-small")
    assert "new_escalation_required" in target["regression_reason_codes"]
    assert comparison["summary"]["dropped_raw_field_count"] >= 2
    assert "private raw model text" not in str(comparison)
    assert "do not store raw response" not in str(comparison)


def test_legal_fixture_regression_warns_on_cost_increase_only():
    passing = _passing_observations()
    comparison = LegalFixtureRegressionService().build_comparison(
        {
            "baseline": {"observations": passing, "run_metadata": _passing_metadata(0.0001)},
            "current": {"observations": passing, "run_metadata": _passing_metadata(0.0002)},
            "policy": {"cost_increase_warn_ratio": 0.25},
        }
    )

    assert comparison["status"] == "warn"
    assert comparison["summary"]["regressed_fixture_count"] == 0
    assert comparison["summary"]["cost_delta_usd"] > 0
    assert comparison["summary"]["cost_delta_ratio"] > 0.25
    assert any("cost delta" in action for action in comparison["recommended_actions"])


def test_legal_fixture_regression_route_returns_comparison():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/fixture-regression")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "not_run"

    passing = _passing_observations()
    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/fixture-regression",
        json={
            "baseline": {"observations": passing},
            "current": {"observations": passing},
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "pass"
