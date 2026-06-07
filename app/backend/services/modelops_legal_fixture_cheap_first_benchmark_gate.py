from __future__ import annotations

import re
from typing import Any

from services.legal_fixture_evidence_bundle import LegalFixtureEvidenceBundleService
from services.legal_fixture_model_matrix import LegalFixtureModelMatrixService
from services.legal_fixture_quick_suite import LegalFixtureQuickSuiteService
from services.legal_fixture_run_report import LegalFixtureRunReportService
from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService
from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.gemini_newapi_cheap_first_calibration import GeminiNewapiCheapFirstCalibrationService
from services.model_budget import COST_TIER_RANK


FORBIDDEN_OUTPUT_KEYS = {
    "input_excerpt",
    "output_text",
    "generated_text",
    "raw_output",
    "raw_response",
    "prompt",
    "messages",
    "authorization",
    "api_key",
    "headers",
}
SENSITIVE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b",
    re.IGNORECASE,
)


class ModelOpsLegalFixtureCheapFirstBenchmarkGateService:
    """Gate cheap-first Gemini default evidence against small legal fixtures."""

    def __init__(
        self,
        quick_suite_service: LegalFixtureQuickSuiteService | None = None,
        model_matrix_service: LegalFixtureModelMatrixService | None = None,
        run_report_service: LegalFixtureRunReportService | None = None,
        evidence_bundle_service: LegalFixtureEvidenceBundleService | None = None,
        document_benchmark_service: LegalDocumentBenchmarkSuiteService | None = None,
        document_coverage_service: LegalDocumentBenchmarkCoverageService | None = None,
        fact_consistency_service: LegalDocumentFactConsistencyBenchmarkService | None = None,
        calibration_service: GeminiNewapiCheapFirstCalibrationService | None = None,
    ) -> None:
        self.quick_suite_service = quick_suite_service or LegalFixtureQuickSuiteService()
        self.model_matrix_service = model_matrix_service or LegalFixtureModelMatrixService()
        self.run_report_service = run_report_service or LegalFixtureRunReportService()
        self.evidence_bundle_service = evidence_bundle_service or LegalFixtureEvidenceBundleService()
        self.document_benchmark_service = document_benchmark_service or LegalDocumentBenchmarkSuiteService()
        self.document_coverage_service = document_coverage_service or LegalDocumentBenchmarkCoverageService()
        self.fact_consistency_service = fact_consistency_service or LegalDocumentFactConsistencyBenchmarkService()
        self.calibration_service = calibration_service or GeminiNewapiCheapFirstCalibrationService()

    def build_gate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        quick_suite = self.quick_suite_service.build_suite()
        model_matrix = self.model_matrix_service.build_matrix()
        run_report = self.run_report_service.build_report(payload)
        evidence_bundle = self.evidence_bundle_service.build_bundle(payload)
        document_evaluation = self.document_benchmark_service.evaluate_outputs(self._document_outputs(payload))
        fact_consistency_evaluation = self.fact_consistency_service.evaluate_outputs(
            self._fact_consistency_outputs(payload)
        )
        document_coverage = self.document_coverage_service.build_matrix()
        calibration = self.calibration_service.build_calibration(self._calibration_payload(payload))
        calibration_by_fixture = self._calibration_by_fixture(calibration)
        matrix_by_fixture = {
            row["fixture_id"]: row
            for row in model_matrix.get("fixtures", [])
            if isinstance(row, dict) and row.get("fixture_id")
        }
        report_by_fixture = {
            row["fixture_id"]: row
            for row in run_report.get("fixture_reports", [])
            if isinstance(row, dict) and row.get("fixture_id")
        }
        source_by_fixture = self._source_by_fixture(quick_suite)
        gate_rows = [
            self._gate_row(
                fixture,
                matrix_by_fixture.get(fixture["fixture_id"]),
                report_by_fixture.get(fixture["fixture_id"]),
                source_by_fixture,
                calibration_by_fixture,
            )
            for fixture in quick_suite.get("selected_fixtures", [])
            if isinstance(fixture, dict)
        ]
        linked_calibration_rows = self._linked_calibration_rows(calibration_by_fixture, gate_rows)
        calibration_blocking_rows = [
            row
            for row in linked_calibration_rows
            if row["status"] == "fail" or row["calibration_decision"] in {"hold_default_change"}
        ]
        calibration_warning_rows = [
            row
            for row in linked_calibration_rows
            if row["status"] == "warn" or row["calibration_decision"] in {"hold_for_fixture_evidence"}
        ]
        blocking_rows = [row for row in gate_rows if row["gate_status"] == "blocked"]
        warning_rows = [row for row in gate_rows if row["gate_status"] in {"review_required", "not_run"}]
        passing_rows = [row for row in gate_rows if row["gate_status"] == "pass"]
        document_benchmark_rows = self._document_benchmark_rows(document_evaluation, document_coverage)
        document_benchmark_status = self._document_benchmark_status(
            document_evaluation,
            document_benchmark_rows,
            document_coverage,
        )
        fact_consistency_rows = self._fact_consistency_rows(fact_consistency_evaluation)
        fact_consistency_status = self._fact_consistency_status(fact_consistency_evaluation, fact_consistency_rows)
        document_blocking_rows = [row for row in document_benchmark_rows if row["gate_status"] == "blocked"]
        document_warning_rows = [
            row for row in document_benchmark_rows if row["gate_status"] in {"review_required", "not_run"}
        ]
        fact_blocking_rows = [row for row in fact_consistency_rows if row["gate_status"] == "blocked"]
        fact_warning_rows = [
            row for row in fact_consistency_rows if row["gate_status"] in {"review_required", "not_run"}
        ]
        default_change_evidence_allowed = (
            bool(gate_rows)
            and all(row["gate_status"] == "pass" for row in gate_rows)
            and document_benchmark_status == "pass"
            and fact_consistency_status == "pass"
            and document_coverage["status"] == "ready"
            and document_coverage["summary"]["missing_document_type_count"] == 0
            and not calibration_blocking_rows
            and not calibration_warning_rows
            and all(row["calibration_status"] == "pass" for row in gate_rows)
        )
        raw_input_field_count = self._raw_input_field_count(payload)

        return {
            "status": self._status(
                gate_rows,
                blocking_rows,
                warning_rows,
                document_benchmark_status,
                fact_consistency_status,
            ),
            "method": {
                "type": "modelops-legal-fixture-cheap-first-benchmark-gate",
                "notes": [
                    "Joins the laptop-safe quick suite, fixture model matrix, run report, evidence bundle, and legal document benchmark suite into one default-change gate.",
                    "Cheap Gemini fixture results can support default retention only after selected fixtures, document benchmark cases, and fact consistency cases pass without high-priority actions.",
                    "The gate returns metadata only and never calls NewAPI, Gemini, OpenAI, Google, a gateway, or the network.",
                ],
            },
            "summary": {
                "selected_fixture_count": len(gate_rows),
                "evaluated_fixture_count": sum(1 for row in gate_rows if row["run_report_status"] != "not_run"),
                "pass_count": len(passing_rows),
                "review_required_count": sum(1 for row in gate_rows if row["gate_status"] == "review_required"),
                "blocked_count": len(blocking_rows),
                "not_run_count": sum(1 for row in gate_rows if row["gate_status"] == "not_run"),
                "default_evidence_allowed_count": len(passing_rows) if default_change_evidence_allowed else 0,
                "default_change_evidence_allowed": default_change_evidence_allowed,
                "cheap_first_model_count": sum(1 for row in gate_rows if row["cheap_first_model"]),
                "premium_escalation_candidate_count": sum(1 for row in gate_rows if row["premium_escalation_candidate"]),
                "license_review_source_count": sum(
                    1
                    for row in gate_rows
                    for state in row["public_source_sampling_states"]
                    if state == "license_review_required"
                ),
                "quick_suite_status": quick_suite["status"],
                "model_matrix_status": model_matrix["status"],
                "run_report_status": run_report["status"],
                "evidence_bundle_status": evidence_bundle["status"],
                "document_benchmark_status": document_benchmark_status,
                "document_benchmark_score": document_evaluation["score"],
                "document_benchmark_case_count": document_evaluation["case_count"],
                "document_benchmark_passed_case_count": document_evaluation["passed_case_count"],
                "document_benchmark_warning_case_count": document_evaluation["warning_case_count"],
                "document_benchmark_failed_case_count": document_evaluation["failed_case_count"],
                "document_benchmark_not_run_case_count": document_evaluation["not_run_case_count"],
                "document_benchmark_blocking_case_count": len(document_blocking_rows),
                "document_benchmark_review_case_count": len(document_warning_rows),
                "fact_consistency_status": fact_consistency_status,
                "fact_consistency_score": fact_consistency_evaluation["score"],
                "fact_consistency_case_count": fact_consistency_evaluation["case_count"],
                "fact_consistency_passed_case_count": fact_consistency_evaluation["passed_case_count"],
                "fact_consistency_warning_case_count": fact_consistency_evaluation["warning_case_count"],
                "fact_consistency_failed_case_count": fact_consistency_evaluation["failed_case_count"],
                "fact_consistency_not_run_case_count": fact_consistency_evaluation["not_run_case_count"],
                "fact_consistency_blocking_case_count": len(fact_blocking_rows),
                "fact_consistency_review_case_count": len(fact_warning_rows),
                "fact_consistency_amount_mismatch_count": fact_consistency_evaluation["amount_mismatch_count"],
                "fact_consistency_deadline_mismatch_count": fact_consistency_evaluation["deadline_mismatch_count"],
                "fact_consistency_contradiction_count": fact_consistency_evaluation["contradiction_count"],
                "calibration_status": calibration["status"],
                "calibration_task_count": len(calibration.get("calibration_rows", [])),
                "linked_calibration_task_count": len(linked_calibration_rows),
                "calibration_blocking_count": len(calibration_blocking_rows),
                "calibration_warning_count": len(calibration_warning_rows),
                "calibration_pass_count": sum(1 for row in linked_calibration_rows if row["status"] == "pass"),
                "calibration_payload_returned": False,
                "document_coverage_status": document_coverage["status"],
                "document_coverage_target_type_count": document_coverage["summary"]["target_document_type_count"],
                "document_coverage_covered_type_count": document_coverage["summary"]["covered_document_type_count"],
                "document_coverage_missing_type_count": document_coverage["summary"]["missing_document_type_count"],
                "estimated_cheap_first_cost_usd": quick_suite["summary"]["estimated_cheap_first_cost_usd"],
                "max_parallel_requests": quick_suite["summary"]["max_parallel_requests"],
                "raw_input_field_count": raw_input_field_count,
                "raw_fixture_text_returned": False,
                "raw_model_output_returned": False,
                "newapi_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "gate_rows": gate_rows,
            "document_benchmark_summary": {
                "status": document_benchmark_status,
                "score": document_evaluation["score"],
                "case_count": document_evaluation["case_count"],
                "passed_case_count": document_evaluation["passed_case_count"],
                "warning_case_count": document_evaluation["warning_case_count"],
                "failed_case_count": document_evaluation["failed_case_count"],
                "not_run_case_count": document_evaluation["not_run_case_count"],
                "blocking_case_count": len(document_blocking_rows),
                "review_case_count": len(document_warning_rows),
                "coverage_status": document_coverage["status"],
                "covered_document_type_count": document_coverage["summary"]["covered_document_type_count"],
                "target_document_type_count": document_coverage["summary"]["target_document_type_count"],
                "missing_document_type_count": document_coverage["summary"]["missing_document_type_count"],
                "max_local_fixtures_per_run": document_coverage["summary"]["max_local_fixtures_per_run"],
                "model_calls": "not_required",
                "network_access": "disabled",
                "raw_document_snippets_returned": False,
                "raw_candidate_text_returned": False,
            },
            "fact_consistency_summary": {
                "status": fact_consistency_status,
                "score": fact_consistency_evaluation["score"],
                "case_count": fact_consistency_evaluation["case_count"],
                "passed_case_count": fact_consistency_evaluation["passed_case_count"],
                "warning_case_count": fact_consistency_evaluation["warning_case_count"],
                "failed_case_count": fact_consistency_evaluation["failed_case_count"],
                "not_run_case_count": fact_consistency_evaluation["not_run_case_count"],
                "blocking_case_count": len(fact_blocking_rows),
                "review_case_count": len(fact_warning_rows),
                "amount_mismatch_count": fact_consistency_evaluation["amount_mismatch_count"],
                "deadline_mismatch_count": fact_consistency_evaluation["deadline_mismatch_count"],
                "contradiction_count": fact_consistency_evaluation["contradiction_count"],
                "raw_input_field_count": fact_consistency_evaluation["raw_input_field_count"],
                "model_calls": "not_required",
                "network_access": "disabled",
                "raw_document_text_returned": False,
                "raw_candidate_text_returned": False,
            },
            "document_benchmark_rows": document_benchmark_rows,
            "fact_consistency_rows": fact_consistency_rows,
            "blocking_fixture_ids": [row["fixture_id"] for row in blocking_rows],
            "review_fixture_ids": [row["fixture_id"] for row in warning_rows],
            "blocking_document_case_ids": [row["case_id"] for row in document_blocking_rows],
            "review_document_case_ids": [row["case_id"] for row in document_warning_rows],
            "blocking_fact_consistency_case_ids": [row["case_id"] for row in fact_blocking_rows],
            "review_fact_consistency_case_ids": [row["case_id"] for row in fact_warning_rows],
            "default_evidence_fixture_ids": [
                row["fixture_id"] for row in passing_rows
            ] if default_change_evidence_allowed else [],
            "default_change_evidence_allowed": default_change_evidence_allowed,
            "routing_policy": {
                "default_strategy": "cheap_first_gemini_with_fixture_gate",
                "cheap_first_models": sorted({row["cheap_first_model"] for row in gate_rows if row["cheap_first_model"]}),
                "default_evidence_requires": [
                    "selected fixture smoke status pass",
                    "no high priority improvement actions",
                    "legal document benchmark suite status pass",
                    "legal document fact consistency status pass",
                    "no document benchmark PII hard block",
                    "no amount, deadline, or contradiction blockers",
                    "linked cheap-first calibration rows pass",
                    "known low-cost cheap-first model ladder",
                    "release evidence bundle reviewed",
                ],
                "blocked_actions": [
                    "do not promote a new default from failed or not-run fixture evidence",
                    "do not promote a new default from failed or not-run legal document benchmark evidence",
                    "do not promote a new default from failed or not-run fact consistency evidence",
                    "do not convert premium escalation candidates into defaults",
                    "do not claim public benchmark scores from metadata-only source mappings",
                ],
                "max_parallel_requests": quick_suite["summary"]["max_parallel_requests"],
                "document_benchmark_required_for_default_change": True,
                "fact_consistency_required_for_default_change": True,
                "calibration_required_for_default_change": True,
                "default_change_evidence_allowed": default_change_evidence_allowed,
                "configuration_write_allowed": False,
                "gateway_call_allowed": False,
                "traffic_shift_allowed": False,
            },
            "recommended_actions": self._recommended_actions(
                blocking_rows,
                warning_rows,
                passing_rows,
                document_benchmark_status,
                document_benchmark_rows,
                fact_consistency_status,
                fact_consistency_rows,
            ),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_fixture_ids": True,
                "returns_document_case_ids": True,
                "returns_fact_consistency_case_ids": True,
                "returns_calibration_task_ids": True,
                "returns_expected_signal_counts": True,
                "returns_calibration_payloads": False,
                "returns_raw_fixture_text": False,
                "returns_fixture_excerpt": False,
                "returns_document_snippets": False,
                "returns_fact_consistency_raw_text": False,
                "returns_candidate_text": False,
                "returns_document_missing_labels": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_called": False,
                "newapi_called": False,
                "output_scope": "fixture ids, document case ids, counts, model ids, cost tiers, gate status, and release actions only",
            },
            "claim_boundary": {
                "automatic_default_change_claimed": False,
                "public_benchmark_scores_claimed": False,
                "legal_document_benchmark_scores_claimed": False,
                "fact_consistency_benchmark_scores_claimed": False,
                "external_dataset_execution_claimed": False,
                "live_gateway_quality_claimed": False,
                "production_legal_accuracy_claimed": False,
                "legal_advice_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py tests/test_gemini_newapi_cheap_first_calibration.py tests/test_gemini_newapi_selector_replay.py tests/test_legal_fixture_quick_suite.py tests/test_legal_fixture_model_matrix.py tests/test_legal_fixture_run_report.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_fact_consistency_benchmark.py -q",
                "npm run typecheck",
                "npm run ui:regression",
            ],
        }

    def _gate_row(
        self,
        fixture: dict[str, Any],
        matrix_row: dict[str, Any] | None,
        report_row: dict[str, Any] | None,
        source_by_fixture: dict[str, list[dict[str, str]]],
        calibration_by_fixture: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        cheap_first = self._cheap_first_candidate(matrix_row)
        report_row = report_row or {}
        linked_calibration_rows = calibration_by_fixture.get(str(fixture["fixture_id"]), [])
        reason_codes = self._reason_codes(
            fixture,
            matrix_row,
            report_row,
            cheap_first,
            source_by_fixture,
            linked_calibration_rows,
        )
        gate_status = self._gate_status(report_row, reason_codes)
        return {
            "id": f"{fixture['fixture_id']}-cheap-first-benchmark-gate",
            "fixture_id": fixture["fixture_id"],
            "title": fixture["title"],
            "matter_type": fixture["matter_type"],
            "task": fixture["task"],
            "cheap_first_model": cheap_first.get("model") if cheap_first else fixture.get("model"),
            "cheap_first_cost_tier": cheap_first.get("cost_tier") if cheap_first else fixture.get("model_cost_tier"),
            "cheap_first_known_model": bool(cheap_first and cheap_first.get("known_model")),
            "estimated_request_cost_usd": fixture["estimated_request_cost_usd"],
            "expected_signal_count": len(fixture.get("expected_signals", [])),
            "expected_task_count": len(fixture.get("expected_tasks", [])),
            "linked_case_count": len(fixture.get("linked_case_ids", [])),
            "public_source_ids": fixture.get("public_source_ids", []),
            "public_source_sampling_states": [
                source["sampling_state"]
                for source in source_by_fixture.get(str(fixture["fixture_id"]), [])
            ],
            "linked_calibration_task_ids": [row["id"] for row in linked_calibration_rows],
            "calibration_status": self._calibration_status(linked_calibration_rows),
            "calibration_decisions": [row["calibration_decision"] for row in linked_calibration_rows],
            "calibration_release_gates": sorted(
                {
                    gate
                    for row in linked_calibration_rows
                    for gate in row.get("release_gate_links", [])
                }
            ),
            "model_matrix_status": (matrix_row or {}).get("status", "missing"),
            "run_report_status": report_row.get("smoke_status", "not_run"),
            "run_report_score": report_row.get("score"),
            "matched_signal_count": report_row.get("matched_signal_count", 0),
            "missing_signal_count": report_row.get("missing_signal_count", len(fixture.get("expected_signals", []))),
            "missing_task_count": report_row.get("missing_task_count", len(fixture.get("expected_tasks", []))),
            "high_priority_action_count": report_row.get("high_priority_action_count", 0),
            "premium_escalation_candidate": self._has_premium_candidate(matrix_row),
            "gate_status": gate_status,
            "release_action": self._release_action(gate_status, report_row),
            "default_change_evidence_allowed": gate_status == "pass",
            "reason_codes": reason_codes,
            "validation_targets": [
                "/api/v1/maintenance/legal-review-benchmark/fixture-run-report",
                "/api/v1/maintenance/legal-review-benchmark/fixture-evidence-bundle",
            ],
            "raw_fixture_text_returned": False,
            "raw_model_output_returned": False,
            "gateway_called": False,
        }

    def _document_outputs(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        for key in ("document_benchmark_outputs", "legal_document_outputs", "document_outputs"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return None

    def _fact_consistency_outputs(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        for key in (
            "document_fact_consistency_outputs",
            "fact_consistency_outputs",
            "legal_document_fact_outputs",
        ):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return None

    def _calibration_payload(self, payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        data = {}
        for key in ("fixture_report", "selector_replay"):
            value = payload.get(key)
            if isinstance(value, dict):
                data[key] = value
        return data or None

    def _document_benchmark_rows(
        self,
        document_evaluation: dict[str, Any],
        document_coverage: dict[str, Any],
    ) -> list[dict[str, Any]]:
        coverage_by_case = {
            row["case_id"]: row
            for row in document_coverage.get("case_rows", [])
            if isinstance(row, dict) and row.get("case_id")
        }
        rows: list[dict[str, Any]] = []
        for result in document_evaluation.get("case_results", []):
            if not isinstance(result, dict):
                continue
            case_id = str(result.get("case_id") or "")
            coverage_row = coverage_by_case.get(case_id, {})
            reason_codes = self._document_reason_codes(result)
            gate_status = self._document_gate_status(result, reason_codes)
            rows.append(
                {
                    "id": f"{case_id}-document-benchmark-gate",
                    "case_id": case_id,
                    "title": str(result.get("title") or coverage_row.get("title") or case_id),
                    "document_type": str(coverage_row.get("document_type") or "unknown"),
                    "matter_type": str(coverage_row.get("matter_type") or "unknown"),
                    "benchmark_status": str(result.get("status") or "not_run"),
                    "gate_status": gate_status,
                    "score": int(result.get("score") or 0),
                    "structure_score": int((result.get("metric_scores") or {}).get("document_structure") or 0),
                    "citation_score": int((result.get("metric_scores") or {}).get("citation_presence") or 0),
                    "pii_score": int((result.get("metric_scores") or {}).get("pii_exclusion") or 0),
                    "risk_score": int((result.get("metric_scores") or {}).get("risk_labeling") or 0),
                    "missing_section_count": len(result.get("missing_sections") or []),
                    "missing_citation_count": len(result.get("missing_citations") or []),
                    "missing_risk_label_count": len(result.get("missing_risk_labels") or []),
                    "pii_finding_count": len(result.get("pii_findings") or []),
                    "hard_pii_block": bool(result.get("hard_pii_block")),
                    "default_change_blocker": gate_status in {"blocked", "not_run"},
                    "reason_codes": reason_codes,
                    "validation_target": "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                    "raw_document_snippet_returned": False,
                    "raw_candidate_text_returned": False,
                }
            )
        return rows

    def _document_reason_codes(self, result: dict[str, Any]) -> list[str]:
        codes: list[str] = []
        status = str(result.get("status") or "not_run")
        if status == "not_run":
            codes.append("document-benchmark-not-run")
        if result.get("hard_pii_block"):
            codes.append("document-pii-hard-block")
        if status == "fail":
            codes.append("document-benchmark-failed")
        if status == "warn":
            codes.append("document-benchmark-warning")
        if result.get("missing_sections"):
            codes.append("missing-document-sections")
        if result.get("missing_citations"):
            codes.append("missing-document-citations")
        if result.get("missing_risk_labels"):
            codes.append("missing-document-risk-labels")
        if status == "pass" and not codes:
            codes.append("document-benchmark-ready")
        return _dedupe(codes)

    def _document_gate_status(self, result: dict[str, Any], reason_codes: list[str]) -> str:
        status = str(result.get("status") or "not_run")
        if status == "not_run":
            return "not_run"
        if "document-pii-hard-block" in reason_codes or status == "fail":
            return "blocked"
        if status == "warn" or any(code.startswith("missing-document-") for code in reason_codes):
            return "review_required"
        return "pass"

    def _document_benchmark_status(
        self,
        document_evaluation: dict[str, Any],
        document_benchmark_rows: list[dict[str, Any]],
        document_coverage: dict[str, Any],
    ) -> str:
        if document_coverage.get("status") != "ready" or document_coverage.get("summary", {}).get(
            "missing_document_type_count", 0
        ):
            return "blocked"
        if document_evaluation.get("status") == "not_run":
            return "not_run"
        if any(row["gate_status"] == "blocked" for row in document_benchmark_rows):
            return "blocked"
        if any(row["gate_status"] in {"review_required", "not_run"} for row in document_benchmark_rows):
            return "review_required"
        return "pass"

    def _fact_consistency_rows(self, fact_consistency_evaluation: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for result in fact_consistency_evaluation.get("case_results", []):
            if not isinstance(result, dict):
                continue
            case_id = str(result.get("case_id") or "")
            reason_codes = [str(item) for item in result.get("reason_codes", [])]
            gate_status = self._fact_consistency_gate_status(result, reason_codes)
            rows.append(
                {
                    "id": f"{case_id}-fact-consistency-gate",
                    "case_id": case_id,
                    "title": str(result.get("title") or case_id),
                    "benchmark_status": str(result.get("status") or "not_run"),
                    "gate_status": gate_status,
                    "score": int(result.get("score") or 0),
                    "amount_score": int((result.get("metric_scores") or {}).get("amount_consistency") or 0),
                    "deadline_score": int((result.get("metric_scores") or {}).get("deadline_consistency") or 0),
                    "fact_score": int((result.get("metric_scores") or {}).get("required_fact_presence") or 0),
                    "contradiction_score": int((result.get("metric_scores") or {}).get("contradiction_exclusion") or 0),
                    "privacy_score": int((result.get("metric_scores") or {}).get("raw_input_exclusion") or 0),
                    "missing_amount_count": len(result.get("missing_amount_ids") or []),
                    "mismatched_amount_count": len(result.get("mismatched_amount_ids") or []),
                    "missing_deadline_count": len(result.get("missing_deadline_ids") or []),
                    "mismatched_deadline_count": len(result.get("mismatched_deadline_ids") or []),
                    "missing_fact_count": len(result.get("missing_fact_ids") or []),
                    "contradiction_count": len(result.get("contradiction_pair_ids") or []),
                    "raw_input_field_count": int(result.get("raw_input_field_count") or 0),
                    "default_change_blocker": gate_status in {"blocked", "not_run"},
                    "reason_codes": reason_codes,
                    "validation_target": "/api/v1/maintenance/legal-review-benchmark/document-fact-consistency",
                    "raw_document_text_returned": False,
                    "raw_candidate_text_returned": False,
                    "gateway_called": False,
                }
            )
        return rows

    def _fact_consistency_gate_status(self, result: dict[str, Any], reason_codes: list[str]) -> str:
        status = str(result.get("status") or "not_run")
        if status == "not_run":
            return "not_run"
        blocking = {
            "amount-mismatch",
            "deadline-mismatch",
            "fact-contradiction",
            "raw-or-sensitive-input-rejected",
        }
        if status == "fail" or bool(result.get("hard_consistency_block")) or any(code in blocking for code in reason_codes):
            return "blocked"
        review = {"amount-missing", "deadline-missing", "required-fact-missing"}
        if status == "warn" or any(code in review for code in reason_codes):
            return "review_required"
        return "pass"

    def _fact_consistency_status(
        self,
        fact_consistency_evaluation: dict[str, Any],
        fact_consistency_rows: list[dict[str, Any]],
    ) -> str:
        if fact_consistency_evaluation.get("status") == "not_run":
            return "not_run"
        if any(row["gate_status"] == "blocked" for row in fact_consistency_rows):
            return "blocked"
        if any(row["gate_status"] in {"review_required", "not_run"} for row in fact_consistency_rows):
            return "review_required"
        return "pass"

    def _source_by_fixture(self, quick_suite: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
        rows: dict[str, list[dict[str, str]]] = {}
        for source in quick_suite.get("public_source_mapping", []):
            if not isinstance(source, dict):
                continue
            for fixture_id in source.get("local_fixture_ids", []):
                rows.setdefault(str(fixture_id), []).append(
                    {
                        "source_id": str(source.get("source_id") or ""),
                        "sampling_state": str(source.get("sampling_state") or "unknown"),
                    }
                )
        return rows

    def _calibration_by_fixture(self, calibration: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        rows: dict[str, list[dict[str, Any]]] = {}
        for row in calibration.get("calibration_rows", []):
            if not isinstance(row, dict):
                continue
            row_data = {
                "id": str(row.get("id") or "unknown-calibration-task"),
                "status": str(row.get("status") or "missing"),
                "calibration_decision": str(row.get("calibration_decision") or "unknown"),
                "release_gate_links": [str(item) for item in row.get("release_gate_links", []) if str(item).strip()],
            }
            for fixture_id in row.get("fixture_ids", []):
                fixture_key = str(fixture_id)
                if fixture_key:
                    rows.setdefault(fixture_key, []).append(row_data)
        return rows

    def _linked_calibration_rows(
        self,
        calibration_by_fixture: dict[str, list[dict[str, Any]]],
        gate_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        seen: set[str] = set()
        rows: list[dict[str, Any]] = []
        for gate_row in gate_rows:
            for row in calibration_by_fixture.get(str(gate_row.get("fixture_id") or ""), []):
                task_id = str(row.get("id") or "")
                if not task_id or task_id in seen:
                    continue
                seen.add(task_id)
                rows.append(row)
        return rows

    def _calibration_status(self, linked_rows: list[dict[str, Any]]) -> str:
        if not linked_rows:
            return "not_mapped"
        if any(row["status"] == "fail" or row["calibration_decision"] == "hold_default_change" for row in linked_rows):
            return "fail"
        if any(
            row["status"] == "warn" or row["calibration_decision"] == "hold_for_fixture_evidence"
            for row in linked_rows
        ):
            return "warn"
        return "pass"

    def _cheap_first_candidate(self, matrix_row: dict[str, Any] | None) -> dict[str, Any] | None:
        for candidate in (matrix_row or {}).get("candidate_ladder", []):
            if isinstance(candidate, dict) and candidate.get("role") == "cheap_first":
                return candidate
        return None

    def _has_premium_candidate(self, matrix_row: dict[str, Any] | None) -> bool:
        return any(
            isinstance(candidate, dict) and candidate.get("cost_tier") == "premium"
            for candidate in (matrix_row or {}).get("candidate_ladder", [])
        )

    def _reason_codes(
        self,
        fixture: dict[str, Any],
        matrix_row: dict[str, Any] | None,
        report_row: dict[str, Any],
        cheap_first: dict[str, Any] | None,
        source_by_fixture: dict[str, list[dict[str, str]]],
        linked_calibration_rows: list[dict[str, Any]],
    ) -> list[str]:
        codes: list[str] = []
        if not report_row or report_row.get("smoke_status") == "not_run":
            codes.append("fixture-not-run")
        if (matrix_row or {}).get("status") != "pass":
            codes.append("fixture-model-ladder-review")
        if not cheap_first:
            codes.append("missing-cheap-first-model")
        elif not cheap_first.get("known_model"):
            codes.append("unknown-cheap-first-model")
        elif COST_TIER_RANK.get(str(cheap_first.get("cost_tier") or "unknown"), 99) <= COST_TIER_RANK.get("low", 99):
            codes.append("known-low-cost-gemini-cheap-first")
        else:
            codes.append("cheap-first-cost-tier-review")
        if report_row.get("smoke_status") == "fail":
            codes.append("fixture-smoke-failed")
        if report_row.get("smoke_status") == "warn":
            codes.append("fixture-smoke-warning")
        if int(report_row.get("high_priority_action_count") or 0) > 0:
            codes.append("high-priority-fixture-improvement")
        if int(report_row.get("missing_signal_count") or 0) > 0:
            codes.append("missing-expected-signals")
        if self._has_premium_candidate(matrix_row):
            codes.append("premium-escalation-candidate")
        if any(
            source["sampling_state"] == "license_review_required"
            for source in source_by_fixture.get(str(fixture["fixture_id"]), [])
        ):
            codes.append("public-source-license-review")
        calibration_status = self._calibration_status(linked_calibration_rows)
        if calibration_status == "not_mapped":
            codes.append("cheap-first-calibration-missing")
        elif calibration_status == "fail":
            codes.append("cheap-first-calibration-blocked")
        elif calibration_status == "warn":
            codes.append("cheap-first-calibration-attention-required")
        else:
            codes.append("cheap-first-calibration-pass")
        return _dedupe(codes) or ["fixture-gate-ready"]

    def _gate_status(self, report_row: dict[str, Any], reason_codes: list[str]) -> str:
        if not report_row or "fixture-not-run" in reason_codes:
            return "not_run"
        blocking = {
            "fixture-smoke-failed",
            "high-priority-fixture-improvement",
            "missing-cheap-first-model",
            "cheap-first-calibration-blocked",
        }
        if any(code in blocking for code in reason_codes):
            return "blocked"
        review = {
            "fixture-model-ladder-review",
            "unknown-cheap-first-model",
            "cheap-first-cost-tier-review",
            "fixture-smoke-warning",
            "missing-expected-signals",
            "cheap-first-calibration-attention-required",
            "cheap-first-calibration-missing",
        }
        if any(code in review for code in reason_codes):
            return "review_required"
        return "pass"

    def _release_action(self, gate_status: str, report_row: dict[str, Any]) -> str:
        if gate_status == "pass":
            return "allow_cheap_first_fixture_evidence_for_default_retention"
        if gate_status == "blocked":
            return "block_default_change_until_selected_fixture_is_fixed"
        if gate_status == "not_run":
            return "run_selected_cheap_first_fixtures_before_default_change"
        next_step = str(report_row.get("recommended_next_step") or "review_fixture_warning")
        return f"review_fixture_before_default_change:{next_step}"

    def _status(
        self,
        gate_rows: list[dict[str, Any]],
        blocking_rows: list[dict[str, Any]],
        warning_rows: list[dict[str, Any]],
        document_benchmark_status: str,
        fact_consistency_status: str,
    ) -> str:
        if blocking_rows or document_benchmark_status == "blocked" or fact_consistency_status == "blocked":
            return "blocked"
        if (
            gate_rows
            and all(row["gate_status"] == "pass" for row in gate_rows)
            and document_benchmark_status == "pass"
            and fact_consistency_status == "pass"
        ):
            return "ready"
        if (
            gate_rows
            and all(row["gate_status"] == "not_run" for row in gate_rows)
            and document_benchmark_status == "not_run"
            and fact_consistency_status == "not_run"
        ):
            return "not_run"
        if warning_rows or document_benchmark_status in {"review_required", "not_run"} or fact_consistency_status in {
            "review_required",
            "not_run",
        }:
            return "ready_with_watchlist"
        return "not_run"

    def _raw_input_field_count(self, payload: dict[str, Any] | None) -> int:
        if not isinstance(payload, dict):
            return 0
        return self._count_forbidden(payload)

    def _count_forbidden(self, value: Any) -> int:
        if isinstance(value, dict):
            count = 0
            for key, child in value.items():
                key_text = str(key).lower()
                if key_text in FORBIDDEN_OUTPUT_KEYS:
                    count += 1
                    continue
                count += self._count_forbidden(child)
            return count
        if isinstance(value, list):
            return sum(self._count_forbidden(item) for item in value[:50])
        if isinstance(value, str) and SENSITIVE_PATTERN.search(value):
            return 1
        return 0

    def _recommended_actions(
        self,
        blocking_rows: list[dict[str, Any]],
        warning_rows: list[dict[str, Any]],
        passing_rows: list[dict[str, Any]],
        document_benchmark_status: str,
        document_benchmark_rows: list[dict[str, Any]],
        fact_consistency_status: str,
        fact_consistency_rows: list[dict[str, Any]],
    ) -> list[str]:
        if blocking_rows:
            return [
                f"{row['fixture_id']}: fix blocked cheap-first fixture evidence before changing defaults."
                for row in blocking_rows[:4]
            ]
        document_blockers = [row for row in document_benchmark_rows if row["gate_status"] == "blocked"]
        if document_blockers:
            return [
                f"{row['case_id']}: clear document benchmark blockers before changing cheap-first defaults."
                for row in document_blockers[:4]
            ]
        if warning_rows:
            return [
                "Run or review selected cheap-first fixtures before treating the result as default-change evidence.",
                "Keep public benchmark mappings metadata-only until license review passes.",
            ]
        if document_benchmark_status == "not_run":
            return [
                "Run the legal document benchmark suite before using cheap-first fixture evidence for a default change.",
                "POST document_benchmark_outputs with sections, citations, risk labels, and PII findings only; do not return generated text.",
            ]
        if document_benchmark_status == "review_required":
            return [
                "Review legal document benchmark warnings before changing cheap-first defaults.",
                "Fix missing structure, citation, or risk-label counts while keeping benchmark evidence metadata-only.",
            ]
        fact_blockers = [row for row in fact_consistency_rows if row["gate_status"] == "blocked"]
        if fact_blockers:
            return [
                f"{row['case_id']}: clear amount, deadline, contradiction, or raw-input blockers before changing cheap-first defaults."
                for row in fact_blockers[:4]
            ]
        if fact_consistency_status == "not_run":
            return [
                "Run the legal document fact consistency benchmark before using cheap-first fixture evidence for a default change.",
                "POST structured amounts, deadlines, and fact IDs only; do not return generated text or raw document text.",
            ]
        if fact_consistency_status == "review_required":
            return [
                "Review legal document fact consistency warnings before changing cheap-first defaults.",
                "Fix missing amount, deadline, or required fact IDs while keeping benchmark evidence metadata-only.",
            ]
        if passing_rows:
            return [
                "Selected legal fixtures, document benchmark cases, and fact consistency cases passed the cheap-first gate; keep defaults cheap-first and archive the evidence bundle.",
                "Do not promote premium escalation candidates into defaults from this gate alone.",
            ]
        return ["Prepare selected fixture observations before evaluating the cheap-first benchmark gate."]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
