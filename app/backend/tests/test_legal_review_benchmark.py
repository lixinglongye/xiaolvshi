from services.legal_review_benchmark import LegalReviewBenchmarkService


def test_legal_review_benchmark_suite_covers_core_task_families():
    suite = LegalReviewBenchmarkService().build_suite()

    assert suite["status"] == "ready"
    assert suite["case_count"] >= 6
    assert "issue_spotting" in suite["task_family_counts"]
    assert "retrieval_grounding" in suite["task_family_counts"]
    assert "safety" in suite["task_family_counts"]
    assert "citation_grounding" in suite["required_metric_counts"]
    assert "cost_route" in suite["required_metric_counts"]
    assert "sk-" not in str(suite)


def test_legal_review_benchmark_catalogs_public_sources_without_downloading():
    suite = LegalReviewBenchmarkService().build_suite()
    source_ids = {source["id"] for source in suite["public_sources"]}

    assert {"legalbench", "cuad", "lexglue", "pile-of-law"}.issubset(source_ids)
    assert suite["public_source_count"] == len(suite["public_sources"])
    assert all("download" not in source["import_policy"].lower() for source in suite["public_sources"])
    assert any("license" in source["license_note"].lower() for source in suite["public_sources"])


def test_legal_review_benchmark_includes_small_local_document_fixtures():
    suite = LegalReviewBenchmarkService().build_suite()
    fixtures = suite["document_fixtures"]
    linked_case_ids = {
        case_id
        for fixture in fixtures
        for case_id in fixture["linked_case_ids"]
    }

    assert suite["document_fixture_count"] >= 4
    assert {"service-contract-risk", "lease-dispute-evidence", "long-pdf-extraction"}.issubset(linked_case_ids)
    assert "instruction-injection-upload" in linked_case_ids
    assert all(fixture["license_note"] == "synthetic-local-fixture" for fixture in fixtures)
    assert all(len(fixture["sample_text"]) < 900 for fixture in fixtures)
    assert "sk-" not in str(fixtures)
    assert "@" not in str(fixtures)


def test_legal_review_benchmark_document_fixtures_map_to_known_cases():
    suite = LegalReviewBenchmarkService().build_suite()
    known_case_ids = {case["id"] for case in suite["cases"]}

    for fixture in suite["document_fixtures"]:
        assert fixture["linked_case_ids"]
        assert set(fixture["linked_case_ids"]).issubset(known_case_ids)
        assert fixture["expected_tasks"]
        assert fixture["expected_signals"]


def test_legal_review_benchmark_default_evaluation_is_not_run():
    result = LegalReviewBenchmarkService().evaluate()

    assert result["status"] == "not_run"
    assert result["score"] == 0
    assert result["not_run_case_count"] == result["case_count"]
    assert result["recommended_actions"]


def test_legal_review_benchmark_passes_complete_run():
    service = LegalReviewBenchmarkService()
    suite = service.build_suite()
    run_results = {
        case["id"]: {metric: "pass" for metric in case["required_metrics"]}
        for case in suite["cases"]
    }

    result = service.evaluate(run_results)

    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["passed_case_count"] == result["case_count"]
    assert result["blocking_case_ids"] == []


def test_legal_review_benchmark_blocks_missing_required_metric():
    service = LegalReviewBenchmarkService()
    suite = service.build_suite()
    run_results = {
        case["id"]: {metric: "pass" for metric in case["required_metrics"]}
        for case in suite["cases"]
    }
    run_results["legal-rag-grounding"]["citation_grounding"] = "fail"

    result = service.evaluate(run_results)

    assert result["status"] == "fail"
    assert "legal-rag-grounding" in result["blocking_case_ids"]
    failed = next(item for item in result["case_results"] if item["case_id"] == "legal-rag-grounding")
    assert "citation_grounding" in failed["missing_metrics"]


def test_legal_review_benchmark_route_returns_suite():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)

    response = testclient.TestClient(app).get("/api/v1/maintenance/legal-review-benchmark")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["suite"]["case_count"] >= 6
