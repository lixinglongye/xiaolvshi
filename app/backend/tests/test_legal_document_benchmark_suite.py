import json
import re

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService


SENSITIVE_PATTERNS = (
    r"sk-[A-Za-z0-9]{12,}",
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{17}[\dXx]\b",
)


def _passing_outputs(suite):
    return {
        case["id"]: {
            "sections": {section: "present" for section in case["required_sections"]},
            "citations": case["expected_citations"],
            "risk_labels": case["expected_risk_labels"],
            "pii_findings": [],
            "generated_text": "Synthetic redacted output only.",
        }
        for case in suite["benchmark_cases"]
    }


def test_legal_document_benchmark_suite_is_laptop_safe_and_small():
    suite = LegalDocumentBenchmarkSuiteService().build_suite()

    assert suite["status"] == "ready"
    assert suite["summary"]["case_count"] == 3
    assert suite["summary"]["check_count"] == 4
    assert suite["summary"]["language"] == "zh-CN"
    assert suite["summary"]["model_calls"] == "not_required"
    assert suite["summary"]["network_access"] == "disabled"
    assert suite["summary"]["data_source"] == "synthetic_inline_fixtures"
    assert suite["resource_policy"]["profile"] == "laptop_safe"
    assert suite["resource_policy"]["external_datasets"] == "disabled"
    assert suite["resource_policy"]["external_model_calls"] == "disabled"
    assert all(0 < len(case["snippet"]) <= 420 for case in suite["benchmark_cases"])


def test_legal_document_benchmark_suite_covers_structure_citations_pii_and_risk():
    suite = LegalDocumentBenchmarkSuiteService().build_suite()
    check_ids = {check["id"] for check in suite["checks"]}
    document_types = {case["document_type"] for case in suite["benchmark_cases"]}

    assert check_ids == {
        "document_structure",
        "citation_presence",
        "pii_exclusion",
        "risk_labeling",
    }
    assert {"civil_complaint", "lawyer_letter", "contract_review"} == document_types
    assert any(check["hard_fail"] is True for check in suite["checks"] if check["id"] == "pii_exclusion")

    for case in suite["benchmark_cases"]:
        assert len(case["required_sections"]) >= 5
        assert len(case["expected_citations"]) >= 2
        assert len(case["expected_risk_labels"]) >= 3
        assert {"identity_number", "mobile_phone", "email", "api_key"}.issubset(case["banned_pii_categories"])


def test_legal_document_benchmark_suite_fixture_boundary_has_no_sensitive_values():
    suite = LegalDocumentBenchmarkSuiteService().build_suite()
    serialized = json.dumps(suite, ensure_ascii=False)

    for pattern in SENSITIVE_PATTERNS:
        assert re.search(pattern, serialized) is None
    assert "real_client_documents" in suite["fixture_content_boundary"]["disallowed"]
    assert "raw_model_outputs" in suite["fixture_content_boundary"]["disallowed"]
    assert "downloaded_public_dataset_rows" in suite["fixture_content_boundary"]["disallowed"]
    assert suite["validation_commands"] == [
        "cd app/backend && python -m pytest tests/test_legal_document_benchmark_suite.py -q"
    ]


def test_legal_document_benchmark_suite_default_evaluation_is_not_run():
    result = LegalDocumentBenchmarkSuiteService().evaluate_outputs()

    assert result["status"] == "not_run"
    assert result["score"] == 0
    assert result["not_run_case_count"] == result["case_count"]
    assert result["blocking_case_ids"] == []


def test_legal_document_benchmark_suite_passes_complete_outputs():
    service = LegalDocumentBenchmarkSuiteService()
    suite = service.build_suite()
    result = service.evaluate_outputs(_passing_outputs(suite))

    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["passed_case_count"] == result["case_count"]
    assert result["blocking_case_ids"] == []
    assert all(case_result["pii_findings"] == [] for case_result in result["case_results"])


def test_legal_document_benchmark_suite_fails_missing_citation_and_pii():
    service = LegalDocumentBenchmarkSuiteService()
    suite = service.build_suite()
    outputs = _passing_outputs(suite)
    target_case = suite["benchmark_cases"][0]
    outputs[target_case["id"]]["citations"] = target_case["expected_citations"][:1]
    outputs[target_case["id"]]["generated_text"] = "\u8054\u7cfb 13812345678"

    result = service.evaluate_outputs(outputs)

    assert result["status"] == "fail"
    assert target_case["id"] in result["blocking_case_ids"]
    failed = next(item for item in result["case_results"] if item["case_id"] == target_case["id"])
    assert failed["status"] == "fail"
    assert failed["hard_pii_block"] is True
    assert failed["metric_scores"]["pii_exclusion"] == 0
    assert failed["missing_citations"] == [target_case["expected_citations"][1]]
    assert "mobile_phone" in failed["pii_findings"]


def test_legal_document_benchmark_suite_accepts_section_dicts_or_lists():
    service = LegalDocumentBenchmarkSuiteService()
    suite = service.build_suite()
    outputs = _passing_outputs(suite)
    target_case = suite["benchmark_cases"][1]
    outputs[target_case["id"]]["sections"] = [{"id": section} for section in target_case["required_sections"]]

    result = service.evaluate_outputs(outputs)
    target_result = next(item for item in result["case_results"] if item["case_id"] == target_case["id"])

    assert result["status"] == "pass"
    assert target_result["metric_scores"]["document_structure"] == 100
