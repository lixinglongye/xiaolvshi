from services.legal_fixture_evidence_bundle import LegalFixtureEvidenceBundleService
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


def test_legal_fixture_evidence_bundle_builds_not_run_template():
    bundle = LegalFixtureEvidenceBundleService().build_bundle()

    assert bundle["status"] == "not_run"
    assert bundle["summary"]["component_count"] >= 8
    assert bundle["summary"]["not_run_component_count"] >= 1
    assert any(item["id"] == "fixture-evidence-bundle" for item in bundle["artifacts"])
    assert bundle["validation_commands"]
    assert "sk-" not in str(bundle)


def test_legal_fixture_evidence_bundle_is_ready_when_observations_pass():
    bundle = LegalFixtureEvidenceBundleService().build_bundle({"observations": _passing_observations()})

    assert bundle["status"] == "ready"
    assert bundle["summary"]["release_decision"] == "keep_cheap_first_defaults"
    assert bundle["summary"]["observed_fixture_count"] == bundle["summary"]["fixture_count"]
    assert bundle["release_claims"]["claim_after_run"][0].startswith("Cheap-first fixture outputs passed")
    assert any("Archive this evidence bundle" in action for action in bundle["recommended_actions"])


def test_legal_fixture_evidence_bundle_blocks_when_fixture_report_needs_escalation():
    bundle = LegalFixtureEvidenceBundleService().build_bundle(
        {
            "observations": {
                "fixture-service-agreement-small": {
                    "route": "fast",
                    "output_text": "risk_matrix",
                }
            }
        }
    )

    assert bundle["status"] == "blocked"
    assert bundle["summary"]["release_decision"] == "hold_default_changes_and_fix_selected_fixtures"
    assert any("run_report" in action for action in bundle["recommended_actions"])


def test_legal_fixture_evidence_bundle_route_returns_bundle():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["status"] == "not_run"

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
        json={"observations": _passing_observations()},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["status"] == "ready"
