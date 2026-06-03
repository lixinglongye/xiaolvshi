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
