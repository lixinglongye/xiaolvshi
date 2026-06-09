from __future__ import annotations

import re
from typing import Any

from services.final_document_delivery_release_gate import FinalDocumentDeliveryReleaseGateService
from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import (
    LegalDocumentFactConsistencyBenchmarkService,
)
from services.small_legal_document_corpus_expansion import SmallLegalDocumentCorpusExpansionService


RAW_INPUT_FIELD_NAMES = {
    "api_key",
    "authorization",
    "client_email",
    "content",
    "credential",
    "credentials",
    "document_text",
    "fixture_text",
    "generated_text",
    "gateway_payload",
    "gateway_response",
    "headers",
    "identity_number",
    "messages",
    "output_text",
    "phone",
    "prompt",
    "raw_output",
    "raw_response",
    "secret",
}

SENSITIVE_VALUE_PATTERN = re.compile(
    r"sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|\b\d{17}[\dXx]\b",
    re.IGNORECASE,
)


class SmallLegalDocumentBenchmarkRunbookEvidenceService:
    """Join tiny legal-document benchmark checks into one delivery runbook packet."""

    def __init__(
        self,
        corpus_service: SmallLegalDocumentCorpusExpansionService | None = None,
        document_service: LegalDocumentBenchmarkSuiteService | None = None,
        fact_service: LegalDocumentFactConsistencyBenchmarkService | None = None,
        delivery_gate_service: FinalDocumentDeliveryReleaseGateService | None = None,
    ) -> None:
        self.corpus_service = corpus_service or SmallLegalDocumentCorpusExpansionService()
        self.document_service = document_service or LegalDocumentBenchmarkSuiteService()
        self.fact_service = fact_service or LegalDocumentFactConsistencyBenchmarkService()
        self.delivery_gate_service = delivery_gate_service or FinalDocumentDeliveryReleaseGateService()

    def build_evidence(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        source = payload if isinstance(payload, dict) else {}
        corpus = self.corpus_service.build_corpus()
        document_suite = self.document_service.build_suite()
        fact_suite = self.fact_service.build_suite()
        document_evaluation = self.document_service.evaluate_outputs(
            self._mapping(source.get("document_benchmark_outputs"))
        )
        fact_evaluation = self.fact_service.evaluate_outputs(
            self._mapping(source.get("document_fact_consistency_outputs"))
        )
        delivery_gate_payload = source.get("final_delivery_payload")
        delivery_gate = self.delivery_gate_service.build_gate(
            self._mapping(delivery_gate_payload) if isinstance(delivery_gate_payload, dict) else None
        )

        document_rows = self._document_rows(document_suite, document_evaluation)
        fact_rows = self._fact_rows(fact_suite, fact_evaluation)
        delivery_rows = self._delivery_rows(delivery_gate)
        evidence_rows = [*document_rows, *fact_rows, *delivery_rows]
        raw_input_field_count = self._raw_input_field_count(source)
        checks = self._checks(corpus, document_evaluation, fact_evaluation, delivery_gate)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "ready")

        return {
            "id": "small-legal-document-benchmark-runbook-evidence",
            "status": status,
            "method": {
                "type": "small-legal-document-benchmark-runbook-evidence",
                "notes": [
                    "Turns public legal benchmark lessons into a small local delivery benchmark packet.",
                    "Joins document structure, citation, fact consistency, and final delivery gates.",
                    "Uses only synthetic IDs, counts, statuses, and reviewer actions; raw documents and model output are never returned.",
                ],
            },
            "summary": {
                "corpus_item_count": corpus["summary"]["corpus_item_count"],
                "document_case_count": document_evaluation["case_count"],
                "document_passed_case_count": document_evaluation["passed_case_count"],
                "document_not_run_case_count": document_evaluation["not_run_case_count"],
                "fact_case_count": fact_evaluation["case_count"],
                "fact_passed_case_count": fact_evaluation["passed_case_count"],
                "fact_not_run_case_count": fact_evaluation["not_run_case_count"],
                "delivery_component_count": delivery_gate["summary"]["component_gate_count"],
                "delivery_ready_component_count": delivery_gate["summary"]["ready_component_count"],
                "ready_evidence_row_count": sum(1 for row in evidence_rows if row["status"] in {"pass", "ready"}),
                "blocked_evidence_row_count": sum(
                    1 for row in evidence_rows if row["status"] in {"fail", "blocked"}
                ),
                "review_required_evidence_row_count": sum(
                    1 for row in evidence_rows if row["status"] in {"warn", "not_run", "template", "review_required"}
                ),
                "raw_input_field_count": raw_input_field_count,
                "max_parallel_requests": 1,
                "model_calls": "not_required",
                "network_access": "disabled",
                "public_benchmark_score_claimed": False,
                "production_quality_claimed": False,
                "raw_payload_returned": False,
            },
            "runbook_steps": self._runbook_steps(),
            "evidence_rows": evidence_rows,
            "document_benchmark_rows": document_rows,
            "fact_consistency_rows": fact_rows,
            "delivery_gate_rows": delivery_rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "source_endpoints": {
                "small_corpus": "/api/v1/maintenance/legal-review-benchmark/small-corpus-expansion",
                "document_benchmark": "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                "fact_consistency": "/api/v1/maintenance/legal-review-benchmark/document-fact-consistency",
                "final_delivery_gate": "/api/v1/maintenance/final-document-delivery-release-gate",
                "runbook_evidence": "/api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence",
            },
            "recommended_actions": self._recommended_actions(status, document_evaluation, fact_evaluation, delivery_gate),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_case_ids": True,
                "returns_document_case_ids": True,
                "returns_fact_consistency_case_ids": True,
                "returns_delivery_component_ids": True,
                "returns_document_snippets": False,
                "returns_fixture_snippets": False,
                "returns_public_benchmark_text": False,
                "returns_raw_document_text": False,
                "returns_generated_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_gateway_payloads": False,
                "returns_credentials": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "production_legal_quality_claimed": False,
                "client_document_coverage_claimed": False,
                "final_document_generated": False,
                "client_delivery_sent": False,
                "legal_advice_claimed": False,
                "allowed_claim": "Small local benchmark runbook evidence for synthetic legal-document delivery readiness.",
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_small_legal_document_benchmark_runbook_evidence.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_suite.py tests/test_legal_document_fact_consistency_benchmark.py tests/test_final_document_delivery_release_gate.py -q",
            ],
        }

    def _document_rows(
        self,
        suite: dict[str, Any],
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result_by_id = {
            str(row["case_id"]): row
            for row in evaluation.get("case_results", [])
            if isinstance(row, dict) and row.get("case_id")
        }
        rows: list[dict[str, Any]] = []
        for case in suite.get("benchmark_cases", []):
            if not isinstance(case, dict) or not case.get("id"):
                continue
            result = result_by_id.get(str(case["id"]), {})
            rows.append(
                {
                    "id": f"document-{case['id']}",
                    "source": "legal_document_benchmark_suite",
                    "case_id": case["id"],
                    "document_type": case.get("document_type"),
                    "matter_type": case.get("matter_type"),
                    "status": result.get("status", "not_run"),
                    "score": result.get("score", 0),
                    "required_section_count": len(case.get("required_sections") or []),
                    "expected_citation_count": len(case.get("expected_citations") or []),
                    "expected_risk_label_count": len(case.get("expected_risk_labels") or []),
                    "missing_section_count": len(result.get("missing_sections") or []),
                    "missing_citation_count": len(result.get("missing_citations") or []),
                    "missing_risk_label_count": len(result.get("missing_risk_labels") or []),
                    "hard_block": bool(result.get("hard_pii_block")),
                    "raw_document_snippet_returned": False,
                    "candidate_text_returned": False,
                }
            )
        return rows

    def _fact_rows(
        self,
        suite: dict[str, Any],
        evaluation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result_by_id = {
            str(row["case_id"]): row
            for row in evaluation.get("case_results", [])
            if isinstance(row, dict) and row.get("case_id")
        }
        rows: list[dict[str, Any]] = []
        for case in suite.get("benchmark_cases", []):
            if not isinstance(case, dict) or not case.get("id"):
                continue
            result = result_by_id.get(str(case["id"]), {})
            rows.append(
                {
                    "id": f"fact-{case['id']}",
                    "source": "legal_document_fact_consistency_benchmark",
                    "case_id": case["id"],
                    "document_type": case.get("document_type"),
                    "matter_type": case.get("matter_type"),
                    "status": result.get("status", "not_run"),
                    "score": result.get("score", 0),
                    "amount_expectation_count": len(case.get("amount_expectations") or []),
                    "deadline_expectation_count": len(case.get("deadline_expectations") or []),
                    "required_fact_count": len(case.get("required_fact_ids") or []),
                    "contradiction_pair_count": len(case.get("contradiction_pairs") or []),
                    "mismatched_amount_count": len(result.get("mismatched_amount_ids") or []),
                    "mismatched_deadline_count": len(result.get("mismatched_deadline_ids") or []),
                    "contradiction_count": len(result.get("contradiction_pair_ids") or []),
                    "reason_codes": list(result.get("reason_codes") or []),
                    "hard_block": bool(result.get("hard_consistency_block")),
                    "raw_document_text_returned": False,
                    "candidate_text_returned": False,
                }
            )
        return rows

    def _delivery_rows(self, delivery_gate: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for component in delivery_gate.get("component_gates", []):
            if not isinstance(component, dict) or not component.get("id"):
                continue
            rows.append(
                {
                    "id": f"delivery-{component['id']}",
                    "source": "final_document_delivery_release_gate",
                    "component_id": component["id"],
                    "title": component.get("title"),
                    "status": component.get("status", "template"),
                    "ready": bool(component.get("ready")),
                    "blocks_release": bool(component.get("blocks_release")),
                    "blocking_issue_count": component.get("blocking_issue_count", 0),
                    "blocker_ids": list(component.get("blocker_ids") or []),
                    "raw_document_text_returned": False,
                    "client_contact_returned": False,
                }
            )
        return rows

    def _checks(
        self,
        corpus: dict[str, Any],
        document_evaluation: dict[str, Any],
        fact_evaluation: dict[str, Any],
        delivery_gate: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": "small-corpus-ready",
                "status": "pass" if corpus.get("status") == "ready" else "warn",
                "reason": f"Small corpus status is {corpus.get('status')}.",
            },
            {
                "id": "document-benchmark-run",
                "status": self._evaluation_check_status(document_evaluation.get("status")),
                "reason": f"Document benchmark evaluation status is {document_evaluation.get('status')}.",
            },
            {
                "id": "fact-consistency-run",
                "status": self._evaluation_check_status(fact_evaluation.get("status")),
                "reason": f"Fact consistency evaluation status is {fact_evaluation.get('status')}.",
            },
            {
                "id": "final-delivery-gate-run",
                "status": self._delivery_check_status(delivery_gate.get("status")),
                "reason": f"Final delivery release gate status is {delivery_gate.get('status')}.",
            },
            {
                "id": "serial-low-resource-runbook",
                "status": "pass",
                "reason": "Runbook requires serial local evaluation with max_parallel_requests=1.",
            },
            {
                "id": "metadata-only-output-boundary",
                "status": "pass",
                "reason": "Packet returns IDs, counts, statuses, and reviewer actions only.",
            },
            {
                "id": "public-benchmark-claim-boundary",
                "status": "pass",
                "reason": "Public benchmark sources inform the rubric only; no public score or downloaded sample is claimed.",
            },
        ]

    def _runbook_steps(self) -> list[dict[str, Any]]:
        return [
            {
                "order": 1,
                "id": "select-small-synthetic-document-cases",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/small-corpus-expansion",
                "action": "Select a tiny synthetic legal-document corpus across common user scenarios.",
                "expected_output": "case IDs, document types, task counts, and risk tag counts",
                "model_call": False,
                "network_call": False,
            },
            {
                "order": 2,
                "id": "evaluate-document-structure-citation-risk",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                "action": "Evaluate structure, citation presence, PII exclusion, and risk labels.",
                "expected_output": "document benchmark status, score, and missing-count metadata",
                "model_call": False,
                "network_call": False,
            },
            {
                "order": 3,
                "id": "evaluate-fact-consistency",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/document-fact-consistency",
                "action": "Evaluate amount, deadline, required fact, contradiction, and raw-input exclusion checks.",
                "expected_output": "fact consistency status, score, mismatch counts, and reason codes",
                "model_call": False,
                "network_call": False,
            },
            {
                "order": 4,
                "id": "attach-final-delivery-gate",
                "endpoint": "/api/v1/maintenance/final-document-delivery-release-gate",
                "action": "Attach final package, export, review, and quota gate metadata before delivery.",
                "expected_output": "component gate statuses and release decision flags",
                "model_call": False,
                "network_call": False,
            },
            {
                "order": 5,
                "id": "archive-runbook-evidence",
                "endpoint": "/api/v1/maintenance/legal-review-benchmark/small-document-runbook-evidence",
                "action": "Archive only sanitized IDs, counts, statuses, and validation commands.",
                "expected_output": "reviewable small benchmark runbook evidence packet",
                "model_call": False,
                "network_call": False,
            },
        ]

    def _recommended_actions(
        self,
        status: str,
        document_evaluation: dict[str, Any],
        fact_evaluation: dict[str, Any],
        delivery_gate: dict[str, Any],
    ) -> list[str]:
        if status == "ready":
            return [
                "Archive this small legal-document benchmark packet with release readiness before client delivery."
            ]

        actions: list[str] = []
        if document_evaluation.get("status") == "not_run":
            actions.append("Run the local document structure/citation/risk benchmark before using this packet.")
        elif document_evaluation.get("status") == "fail":
            actions.append("Fix blocking document benchmark cases before final delivery review.")

        if fact_evaluation.get("status") == "not_run":
            actions.append("Run the structured fact consistency benchmark before using this packet.")
        elif fact_evaluation.get("status") == "fail":
            actions.append("Fix amount, deadline, contradiction, or raw-input fact consistency blockers.")

        if delivery_gate.get("status") == "template":
            actions.append("Attach sanitized final delivery metadata before claiming release readiness.")
        elif delivery_gate.get("status") == "blocked":
            actions.append("Resolve final delivery component blockers before client delivery.")

        return actions or ["Review warning benchmark rows before release."]

    def _evaluation_check_status(self, status: Any) -> str:
        if status == "pass":
            return "pass"
        if status == "fail":
            return "fail"
        return "warn"

    def _delivery_check_status(self, status: Any) -> str:
        if status == "ready":
            return "pass"
        if status == "blocked":
            return "fail"
        return "warn"

    def _mapping(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _raw_input_field_count(self, value: Any) -> int:
        if isinstance(value, dict):
            return sum(1 for key in value if str(key).lower() in RAW_INPUT_FIELD_NAMES) + sum(
                self._raw_input_field_count(item) for item in value.values()
            )
        if isinstance(value, list):
            return sum(self._raw_input_field_count(item) for item in value)
        if isinstance(value, str) and SENSITIVE_VALUE_PATTERN.search(value):
            return 1
        return 0
