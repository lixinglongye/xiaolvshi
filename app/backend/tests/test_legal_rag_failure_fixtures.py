import re

from services.legal_rag_failure_fixtures import LegalRagFailureFixturesService


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{20,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def _complete_observations(service: LegalRagFailureFixturesService) -> dict[str, dict[str, object]]:
    suite = service.build_suite()
    observations = {}
    for case in suite["fixture_cases"]:
        observations[case["id"]] = {
            "detected_failure_labels": case["expected_failure_labels"],
            "evidence_signals": case["expected_evidence_signals"],
            "recommended_actions": case["acceptable_actions"],
            "released_to_user": False,
        }
    return observations


def test_legal_rag_failure_fixtures_build_small_local_suite():
    suite = LegalRagFailureFixturesService().build_suite()

    assert suite["status"] == "ready"
    assert suite["summary"]["fixture_case_count"] == 6
    assert suite["summary"]["taxonomy_count"] == 6
    assert suite["summary"]["model_calls"] == "not_required"
    assert suite["summary"]["network_access"] == "disabled"
    assert suite["fixture_cases"]
    assert suite["failure_taxonomy"]


def test_legal_rag_failure_fixtures_cover_required_failure_modes():
    suite = LegalRagFailureFixturesService().build_suite()
    labels = {
        label
        for case in suite["fixture_cases"]
        for label in case["expected_failure_labels"]
    }
    taxonomy_ids = {item["id"] for item in suite["failure_taxonomy"]}

    assert {
        "missing_citation",
        "stale_regulation",
        "jurisdiction_mismatch",
        "unsupported_conclusion",
        "hallucinated_article",
        "conflicting_facts",
    }.issubset(labels)
    assert labels.issubset(taxonomy_ids)


def test_legal_rag_failure_evaluation_rules_are_low_resource_and_local_only():
    suite = LegalRagFailureFixturesService().build_suite()
    rules = suite["evaluation_rules"]

    assert rules["model_call_policy"] == "never_call_external_models"
    assert rules["network_access"] == "disabled"
    assert rules["resource_profile"]["parallelism"] == 1
    assert rules["resource_profile"]["max_cases"] == 6
    assert suite["summary"]["max_context_items_per_case"] <= 2
    assert suite["summary"]["max_context_chars"] < 1000
    assert suite["validation_commands"] == [
        "cd app/backend && python -m pytest tests/test_legal_rag_failure_fixtures.py -q"
    ]


def test_legal_rag_failure_fixtures_contain_no_sensitive_information():
    suite = LegalRagFailureFixturesService().build_suite()
    suite_text = str(suite)

    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, suite_text)
    assert "synthetic" in suite["privacy_note"]
    assert "API keys" in suite["privacy_note"]


def test_legal_rag_failure_default_evaluation_is_not_run():
    result = LegalRagFailureFixturesService().evaluate_observations()

    assert result["status"] == "not_run"
    assert result["score"] == 0
    assert result["not_run_case_count"] == result["case_count"]
    assert result["blocking_case_ids"] == []


def test_legal_rag_failure_evaluation_passes_complete_observations():
    service = LegalRagFailureFixturesService()
    result = service.evaluate_observations(_complete_observations(service))

    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["passed_case_count"] == result["case_count"]
    assert result["blocking_case_ids"] == []


def test_legal_rag_failure_evaluation_warns_partial_but_blocked_observations():
    service = LegalRagFailureFixturesService()
    observations = _complete_observations(service)
    first_case_id = service.build_suite()["fixture_cases"][0]["id"]
    observations[first_case_id] = {
        "detected_failure_labels": ["missing_citation"],
        "evidence_signals": [],
        "recommended_actions": ["block_final_answer"],
        "released_to_user": False,
    }

    result = service.evaluate_observations(observations)

    assert result["status"] == "warn"
    warning = next(item for item in result["case_results"] if item["case_id"] == first_case_id)
    assert warning["status"] == "warn"
    assert warning["missing_evidence_signals"] == ["legal_conclusion_without_source_id"]


def test_legal_rag_failure_evaluation_fails_unsafe_release():
    service = LegalRagFailureFixturesService()
    observations = _complete_observations(service)
    first_case_id = service.build_suite()["fixture_cases"][0]["id"]
    observations[first_case_id] = {
        "detected_failure_labels": [],
        "evidence_signals": [],
        "recommended_actions": [],
        "released_to_user": True,
    }

    result = service.evaluate_observations(observations)

    assert result["status"] == "fail"
    assert first_case_id in result["blocking_case_ids"]
    failed = next(item for item in result["case_results"] if item["case_id"] == first_case_id)
    assert failed["status"] == "fail"
    assert failed["metric_scores"]["unsafe_release_blocked"] == 0
    assert failed["missing_failure_labels"] == ["missing_citation"]


def test_legal_rag_failure_fixture_route_returns_suite_and_evaluates_observations():
    import pytest

    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    from routers.maintenance import router

    app = fastapi.FastAPI()
    app.include_router(router)
    client = testclient.TestClient(app)

    suite_response = client.get("/api/v1/maintenance/legal-review-benchmark/rag-failure-fixtures")
    assert suite_response.status_code == 200
    suite_payload = suite_response.json()
    assert suite_payload["success"] is True
    assert suite_payload["data"]["summary"]["fixture_case_count"] == 6

    eval_response = client.post("/api/v1/maintenance/legal-review-benchmark/rag-failure-fixtures", json={})
    assert eval_response.status_code == 200
    eval_payload = eval_response.json()
    assert eval_payload["success"] is True
    assert eval_payload["data"]["status"] == "not_run"
