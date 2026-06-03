from services.legal_fixture_result_archive import LegalFixtureResultArchiveService
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


def test_legal_fixture_result_archive_builds_not_run_template():
    archive = LegalFixtureResultArchiveService().build_archive()

    assert archive["status"] == "not_run"
    assert archive["summary"]["archived_fixture_count"] == 0
    assert archive["archive_record"]["source_endpoint"].endswith("/result-archive")
    assert "output_text" in archive["archive_record"]["excluded_fields"]
    assert "sk-" not in str(archive)


def test_legal_fixture_result_archive_keeps_only_safe_result_summaries():
    archive = LegalFixtureResultArchiveService().build_archive(
        {
            "observations": _passing_observations(),
            "run_metadata": {
                "fixture-service-agreement-small": {
                    "phase": "cheap_first",
                    "model": "gemini-2.5-flash-lite",
                    "estimated_cost_usd": 0.000123,
                    "http_status": 200,
                    "raw_response": {"content": "do not archive this text"},
                }
            },
        }
    )

    assert archive["status"] == "ready"
    assert archive["summary"]["archived_fixture_count"] == archive["summary"]["observed_fixture_count"]
    assert archive["summary"]["dropped_raw_field_count"] >= 2
    assert archive["summary"]["observed_cost_usd"] == 0.000123
    assert archive["request_metadata_summaries"] == [
        {
            "fixture_id": "fixture-service-agreement-small",
            "phase": "cheap_first",
            "model": "gemini-2.5-flash-lite",
            "estimated_cost_usd": 0.000123,
            "http_status": 200,
            "archived_fields": ["phase", "model", "estimated_cost_usd", "http_status"],
        }
    ]
    assert "do not archive this text" not in str(archive)


def test_legal_fixture_result_archive_blocks_when_fixture_report_blocks():
    archive = LegalFixtureResultArchiveService().build_archive(
        {
            "observations": {
                "fixture-service-agreement-small": {
                    "route": "fast",
                    "output_text": "risk_matrix",
                }
            }
        }
    )

    assert archive["status"] == "blocked"
    assert archive["summary"]["release_decision"] == "hold_default_changes_and_fix_selected_fixtures"
    assert any("Resolve fixture-run-report escalations" in action for action in archive["recommended_actions"])


def test_legal_fixture_result_archive_route_returns_archive():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/result-archive")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "not_run"

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/result-archive",
        json={"observations": _passing_observations()},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
