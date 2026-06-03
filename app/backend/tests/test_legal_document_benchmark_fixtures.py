import re

from services.legal_document_benchmark_fixtures import LegalDocumentBenchmarkFixturesService


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{20,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def test_legal_document_benchmark_fixtures_build_small_chinese_suite():
    suite = LegalDocumentBenchmarkFixturesService().build_suite()

    assert suite["status"] == "ready"
    assert 3 <= suite["summary"]["benchmark_case_count"] <= 5
    assert suite["summary"]["language"] == "zh-CN"
    assert suite["summary"]["model_calls"] == "not_required"
    assert suite["summary"]["network_access"] == "disabled"
    assert suite["benchmark_cases"]
    assert all(0 < len(case["snippet"]) <= 500 for case in suite["benchmark_cases"])


def test_legal_document_benchmark_fixtures_cover_core_document_types():
    suite = LegalDocumentBenchmarkFixturesService().build_suite()
    document_types = {case["document_type"] for case in suite["benchmark_cases"]}
    matter_types = {case["matter_type"] for case in suite["benchmark_cases"]}

    assert {"contract", "civil_complaint", "lawyer_letter"}.issubset(document_types)
    assert "service_contract" in matter_types
    assert "private_lending_dispute" in matter_types
    assert "lease_payment_collection" in matter_types


def test_legal_document_benchmark_expected_tasks_cover_classification_extraction_and_risk():
    suite = LegalDocumentBenchmarkFixturesService().build_suite()
    task_ids = {task["id"] for task in suite["expected_tasks"]}

    assert {
        "document_classification",
        "party_extraction",
        "amount_or_claim_extraction",
        "deadline_extraction",
        "risk_labeling",
    }.issubset(task_ids)
    for case in suite["benchmark_cases"]:
        assert set(case["expected_tasks"]).issubset(task_ids)
        assert case["expected_fields"]
        assert case["expected_risk_labels"]
        assert case["expected_classification_labels"]


def test_legal_document_benchmark_contains_no_sensitive_information():
    suite = LegalDocumentBenchmarkFixturesService().build_suite()
    suite_text = str(suite)

    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, suite_text)
    assert "API key" in suite["privacy_note"]
    assert "raw model outputs" in suite["privacy_note"]


def test_legal_document_benchmark_evaluation_plan_is_local_only():
    suite = LegalDocumentBenchmarkFixturesService().build_suite()
    plan = suite["evaluation_plan"]

    assert plan["model_call_policy"] == "never_call_external_models"
    assert plan["network_access"] == "disabled"
    assert plan["resource_profile"]["parallelism"] == 1
    assert suite["validation_commands"] == [
        "cd app/backend && python -m pytest tests/test_legal_document_benchmark_fixtures.py -q"
    ]


def test_legal_document_benchmark_default_evaluation_is_not_run():
    result = LegalDocumentBenchmarkFixturesService().evaluate_predictions()

    assert result["status"] == "not_run"
    assert result["score"] == 0
    assert result["not_run_case_count"] == result["case_count"]
    assert result["blocking_case_ids"] == []


def test_legal_document_benchmark_passes_complete_predictions():
    service = LegalDocumentBenchmarkFixturesService()
    suite = service.build_suite()
    predictions = {}
    for case in suite["benchmark_cases"]:
        predictions[case["id"]] = {
            "document_type": case["document_type"],
            "classification_labels": case["expected_classification_labels"],
            "task_labels": case["expected_tasks"],
            "risk_labels": case["expected_risk_labels"],
            "extracted_fields": case["expected_fields"],
        }

    result = service.evaluate_predictions(predictions)

    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["passed_case_count"] == result["case_count"]
    assert result["blocking_case_ids"] == []


def test_legal_document_benchmark_fails_sparse_prediction():
    service = LegalDocumentBenchmarkFixturesService()
    suite = service.build_suite()
    case = suite["benchmark_cases"][0]

    result = service.evaluate_predictions(
        {
            case["id"]: {
                "document_type": "unknown",
                "task_labels": ["document_classification"],
                "risk_labels": [],
                "extracted_fields": {},
            }
        }
    )

    assert result["status"] == "fail"
    assert case["id"] in result["blocking_case_ids"]
    failed = next(item for item in result["case_results"] if item["case_id"] == case["id"])
    assert failed["missing_risk_labels"]
    assert failed["missing_fields"]


def test_legal_document_benchmark_fixture_route_returns_suite_and_evaluates_predictions():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    suite_response = client.get("/api/v1/maintenance/legal-review-benchmark/document-fixtures")
    assert suite_response.status_code == 200
    suite_payload = suite_response.json()
    assert suite_payload["success"] is True
    assert suite_payload["data"]["summary"]["benchmark_case_count"] >= 3

    eval_response = client.post("/api/v1/maintenance/legal-review-benchmark/document-fixtures", json={})
    assert eval_response.status_code == 200
    eval_payload = eval_response.json()
    assert eval_payload["success"] is True
    assert eval_payload["data"]["status"] == "not_run"
