from services.legal_fixture_run_report import LegalFixtureRunReportService
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


def test_legal_fixture_run_report_is_not_run_without_observations():
    report = LegalFixtureRunReportService().build_report()

    assert report["status"] == "not_run"
    assert report["release_decision"] == "run_cheap_first_fixture_batches"
    assert report["summary"]["observed_fixture_count"] == 0
    assert report["run_evidence_template"]["source_endpoint"].endswith("/fixture-run-report")
    assert "sk-" not in str(report)


def test_legal_fixture_run_report_keeps_cheap_defaults_when_fixture_smoke_passes():
    report = LegalFixtureRunReportService().build_report({"observations": _passing_observations()})

    assert report["status"] == "ready"
    assert report["release_decision"] == "keep_cheap_first_defaults"
    assert report["summary"]["passed_fixture_count"] == report["summary"]["fixture_count"]
    assert report["summary"]["escalation_required_count"] == 0
    assert all(row["recommended_next_step"] == "keep_cheap_first_result" for row in report["fixture_reports"])


def test_legal_fixture_run_report_flags_targeted_escalation_and_improvements():
    report = LegalFixtureRunReportService().build_report(
        {
            "observations": {
                "fixture-service-agreement-small": {
                    "route": "fast",
                    "output_text": "risk_matrix",
                }
            }
        }
    )

    assert report["status"] == "needs_escalation"
    assert report["release_decision"] == "hold_default_changes_and_fix_selected_fixtures"
    assert "fixture-service-agreement-small" in report["escalation_fixture_ids"]
    target = next(row for row in report["fixture_reports"] if row["fixture_id"] == "fixture-service-agreement-small")
    assert target["high_priority_action_count"] >= 1
    assert target["recommended_next_step"] == "apply_high_priority_improvements"


def test_legal_fixture_run_report_accepts_run_metadata_costs():
    report = LegalFixtureRunReportService().build_report(
        {
            "observations": _passing_observations(),
            "run_metadata": {
                "fixture-service-agreement-small": {
                    "phase": "cheap_first",
                    "model": "gemini-2.5-flash-lite",
                    "estimated_cost_usd": 0.000123,
                }
            },
        }
    )

    target = next(row for row in report["fixture_reports"] if row["fixture_id"] == "fixture-service-agreement-small")
    assert target["observed_model"] == "gemini-2.5-flash-lite"
    assert target["observed_cost_usd"] == 0.000123
    assert report["summary"]["observed_cost_usd"] == 0.000123
    assert report["summary"]["observed_request_count"] == 1


def test_legal_fixture_run_report_route_returns_template_and_report():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/fixture-run-report")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "not_run"

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
        json={"observations": _passing_observations()},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
