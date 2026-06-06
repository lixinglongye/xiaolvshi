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

    assert {"legalbench", "cuad", "lexglue", "pile-of-law", "legalbench-rag", "lexeval", "casegen"}.issubset(
        source_ids
    )
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


def test_legal_review_fixture_smoke_template_tracks_all_fixtures():
    service = LegalReviewBenchmarkService()
    suite = service.build_suite()
    template = service.build_fixture_smoke_template()

    assert suite["fixture_smoke_template"]["fixture_count"] == suite["document_fixture_count"]
    assert template["status"] == "ready"
    assert template["fixture_count"] == len(template["default_observations"])
    assert all(row["input_excerpt"] for row in template["fixtures"])


def test_legal_review_fixture_smoke_default_is_not_run():
    result = LegalReviewBenchmarkService().evaluate_fixture_smoke()

    assert result["status"] == "not_run"
    assert result["score"] == 0
    assert result["not_run_fixture_count"] == result["fixture_count"]
    assert result["recommended_actions"]


def test_legal_review_fixture_smoke_passes_complete_observations():
    service = LegalReviewBenchmarkService()
    template = service.build_fixture_smoke_template()
    observations = {}
    for fixture in template["fixtures"]:
        observations[fixture["id"]] = {
            "route": fixture["expected_routes"][0],
            "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
        }

    result = service.evaluate_fixture_smoke(observations)

    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["passed_fixture_count"] == result["fixture_count"]
    assert result["blocking_fixture_ids"] == []


def test_legal_review_fixture_smoke_fails_sparse_observation():
    service = LegalReviewBenchmarkService()
    template = service.build_fixture_smoke_template()
    fixture = template["fixtures"][0]

    result = service.evaluate_fixture_smoke(
        {
            fixture["id"]: {
                "route": "review",
                "output_text": "short summary only",
            }
        }
    )

    assert result["status"] == "fail"
    assert fixture["id"] in result["blocking_fixture_ids"]
    failed = next(item for item in result["fixture_results"] if item["fixture_id"] == fixture["id"])
    assert failed["missing_signals"]
    assert failed["metric_scores"]["route_match"] == 0


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


def test_legal_review_fixture_smoke_routes_return_template_and_evaluation():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    get_response = client.get("/api/v1/maintenance/legal-review-benchmark/fixture-smoke")
    assert get_response.status_code == 200
    template_payload = get_response.json()
    assert template_payload["success"] is True
    assert template_payload["data"]["template"]["fixture_count"] >= 4

    fixture = template_payload["data"]["template"]["fixtures"][0]
    post_response = client.post(
        "/api/v1/maintenance/legal-review-benchmark/fixture-smoke",
        json={
            fixture["id"]: {
                "route": fixture["expected_routes"][0],
                "output_text": " ".join(fixture["expected_signals"] + fixture["expected_tasks"]),
            }
        },
    )
    assert post_response.status_code == 200
    assert post_response.json()["success"] is True
    assert post_response.json()["data"]["fixture_results"][0]["status"] == "pass"
