import re

from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService


def test_public_benchmark_sampler_builds_metadata_only_plan():
    plan = LegalPublicBenchmarkSamplerService().build_plan()

    assert plan["status"] == "ready"
    assert plan["summary"]["source_count"] >= 7
    assert plan["summary"]["license_review_required_source_count"] >= 1
    assert plan["summary"]["catalog_only_source_count"] >= 1
    assert plan["resource_policy"]["network_access"] == "disabled_by_default"
    assert all(item["download_policy"] == "do_not_download_in_default_local_tests" for item in plan["source_plans"])
    assert not re.search(r"sk-[A-Za-z0-9]{20,}", str(plan))
    assert "@" not in str(plan)


def test_public_benchmark_sampler_maps_sources_to_local_fixtures_and_cases():
    plan = LegalPublicBenchmarkSamplerService().build_plan()
    plans_by_id = {item["source_id"]: item for item in plan["source_plans"]}

    assert "fixture-service-agreement-small" in plans_by_id["cuad"]["local_fixture_ids"]
    assert "service-contract-risk" in plans_by_id["cuad"]["benchmark_case_ids"]
    assert "legal-rag-grounding" in plans_by_id["legalbench"]["benchmark_case_ids"]
    assert "legal-rag-grounding" in plans_by_id["legalbench-rag"]["benchmark_case_ids"]
    assert "ldoc-legal-opinion-mini" in plans_by_id["legalbench-rag"]["document_fixture_ids"]
    assert "ldoc-contract-review-mini" in plans_by_id["lexeval"]["document_fixture_ids"]
    assert "ldoc-settlement-agreement-mini" in plans_by_id["casegen"]["document_fixture_ids"]
    assert plans_by_id["pile-of-law"]["sampling_state"] == "catalog_only"
    assert plans_by_id["pile-of-law"]["max_samples"] == 0


def test_public_benchmark_sampler_allows_capped_sampling_after_license_review():
    plan = LegalPublicBenchmarkSamplerService().build_plan(
        {
            "enabled_source_ids": ["cuad", "legalbench"],
            "max_samples_per_source": 4,
            "license_reviews": {
                "cuad": "approved",
                "legalbench": "pass",
            },
        }
    )

    assert plan["summary"]["source_count"] == 2
    assert plan["summary"]["sampling_ready_source_count"] == 2
    assert plan["summary"]["max_samples_per_source"] == 4
    assert all(item["sampling_state"] == "sampling_ready" for item in plan["source_plans"])
    assert all(item["max_samples"] == 4 for item in plan["source_plans"])


def test_public_benchmark_sampler_clamps_local_sample_count():
    plan = LegalPublicBenchmarkSamplerService().build_plan({"max_samples_per_source": 99})

    assert plan["summary"]["max_samples_per_source"] == 5
    assert all(item["max_samples"] <= 5 for item in plan["source_plans"])


def test_public_benchmark_sampler_route_returns_plan():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/public-sampler")
    assert get_response.status_code == 200
    assert get_response.json()["data"]["summary"]["source_count"] >= 7

    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/public-sampler",
        json={"enabled_source_ids": ["cuad"], "license_reviews": {"cuad": "approved"}},
    )
    assert post_response.status_code == 200
    assert post_response.json()["data"]["source_plans"][0]["sampling_state"] == "sampling_ready"
