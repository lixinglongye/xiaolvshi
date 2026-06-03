from services.legal_fixture_quick_suite import LegalFixtureQuickSuiteService


def test_legal_fixture_quick_suite_builds_low_resource_default():
    suite = LegalFixtureQuickSuiteService().build_suite()

    assert suite["status"] == "ready"
    assert suite["summary"]["selected_fixture_count"] == 3
    assert suite["summary"]["available_fixture_count"] >= 4
    assert suite["summary"]["max_parallel_requests"] == 1
    assert suite["summary"]["network_access"] == "disabled_by_default"
    assert 0 < suite["summary"]["estimated_cheap_first_cost_usd"] < 0.01
    assert "sk-" not in str(suite)
    assert list(suite["observation_template"]) == [
        "fixture-service-agreement-small",
        "fixture-lease-dispute-notice-small",
        "fixture-low-text-pdf-page-small",
    ]


def test_legal_fixture_quick_suite_maps_public_sources_without_downloads():
    suite = LegalFixtureQuickSuiteService().build_suite()
    sources_by_id = {source["source_id"]: source for source in suite["public_source_mapping"]}

    assert "cuad" in sources_by_id
    assert "legalbench" in sources_by_id
    assert "pile-of-law" in sources_by_id
    assert sources_by_id["cuad"]["local_fixture_ids"] == ["fixture-service-agreement-small"]
    assert sources_by_id["pile-of-law"]["sampling_state"] == "catalog_only"
    assert all(source["download_policy"] == "do_not_download_in_default_local_tests" for source in sources_by_id.values())
    assert all(source["run_policy"] == "metadata_only_until_license_review_passes" for source in sources_by_id.values())


def test_legal_fixture_quick_suite_clamps_fixture_limit():
    service = LegalFixtureQuickSuiteService()

    small = service.build_suite(0)
    full = service.build_suite(99)

    assert small["summary"]["selected_fixture_count"] == 1
    assert full["summary"]["selected_fixture_count"] == full["summary"]["available_fixture_count"]
    assert "fixture-adversarial-upload-small" in full["observation_template"]


def test_legal_fixture_quick_suite_route_returns_plan():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark/quick-suite?fixture_limit=2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["summary"]["selected_fixture_count"] == 2
    assert payload["data"]["quick_steps"][1]["max_parallel_requests"] == 1
