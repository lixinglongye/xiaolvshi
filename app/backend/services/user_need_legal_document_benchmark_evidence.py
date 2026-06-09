from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_document_benchmark_fixtures import LegalDocumentBenchmarkFixturesService
from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService
from services.legal_document_fact_consistency_benchmark import LegalDocumentFactConsistencyBenchmarkService
from services.modelops_legal_fixture_cheap_first_benchmark_gate import (
    ModelOpsLegalFixtureCheapFirstBenchmarkGateService,
)
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService
from services.user_needs_radar import UserNeedsRadarService


class UserNeedLegalDocumentBenchmarkEvidenceService:
    """Join user needs to local legal-document benchmark evidence."""

    def __init__(
        self,
        user_needs_service: UserNeedsRadarService | None = None,
        benchmark_coverage_service: UserNeedBenchmarkCoverageService | None = None,
        document_coverage_service: LegalDocumentBenchmarkCoverageService | None = None,
        document_suite_service: LegalDocumentBenchmarkSuiteService | None = None,
        document_fixture_service: LegalDocumentBenchmarkFixturesService | None = None,
        fact_consistency_service: LegalDocumentFactConsistencyBenchmarkService | None = None,
        cheap_first_gate_service: ModelOpsLegalFixtureCheapFirstBenchmarkGateService | None = None,
    ) -> None:
        self.user_needs_service = user_needs_service or UserNeedsRadarService()
        self.benchmark_coverage_service = benchmark_coverage_service or UserNeedBenchmarkCoverageService()
        self.document_coverage_service = document_coverage_service or LegalDocumentBenchmarkCoverageService()
        self.document_suite_service = document_suite_service or LegalDocumentBenchmarkSuiteService()
        self.document_fixture_service = document_fixture_service or LegalDocumentBenchmarkFixturesService()
        self.fact_consistency_service = fact_consistency_service or LegalDocumentFactConsistencyBenchmarkService()
        self.cheap_first_gate_service = cheap_first_gate_service or ModelOpsLegalFixtureCheapFirstBenchmarkGateService()

    def build_bridge(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        radar = self.user_needs_service.build_radar()
        user_need_coverage = self.benchmark_coverage_service.build_coverage()
        document_coverage = self.document_coverage_service.build_matrix()
        document_suite = self.document_suite_service.build_suite()
        document_evaluation = self.document_suite_service.evaluate_outputs(
            self._safe_mapping(payload.get("document_benchmark_outputs"))
        )
        fact_suite = self.fact_consistency_service.build_suite()
        fact_evaluation = self.fact_consistency_service.evaluate_outputs(
            self._safe_mapping(payload.get("document_fact_consistency_outputs"))
        )
        local_rule_baseline = self.document_fixture_service.build_local_rule_baseline()
        cheap_first_gate = self.cheap_first_gate_service.build_gate(self._cheap_first_payload(payload))

        document_case_by_id = {
            str(case["id"]): case
            for case in document_suite.get("benchmark_cases", [])
            if isinstance(case, dict) and case.get("id")
        }
        document_coverage_by_id = {
            str(row["case_id"]): row
            for row in document_coverage.get("case_rows", [])
            if isinstance(row, dict) and row.get("case_id")
        }
        document_result_by_id = {
            str(row["case_id"]): row
            for row in document_evaluation.get("case_results", [])
            if isinstance(row, dict) and row.get("case_id")
        }
        baseline_row_by_id = {
            str(row["case_id"]): row
            for row in local_rule_baseline.get("coverage_rows", [])
            if isinstance(row, dict) and row.get("case_id")
        }
        fact_case_by_id = {
            str(case["id"]): case
            for case in fact_suite.get("benchmark_cases", [])
            if isinstance(case, dict) and case.get("id")
        }
        fact_result_by_id = {
            str(row["case_id"]): row
            for row in fact_evaluation.get("case_results", [])
            if isinstance(row, dict) and row.get("case_id")
        }
        coverage_row_by_need_id = {
            str(row["need_id"]): row
            for row in user_need_coverage.get("coverage_rows", [])
            if isinstance(row, dict) and row.get("need_id")
        }

        evidence_rows = [
            self._evidence_row(
                need=need,
                coverage_row=coverage_row_by_need_id.get(str(need["id"]), {}),
                document_case_by_id=document_case_by_id,
                document_coverage_by_id=document_coverage_by_id,
                document_result_by_id=document_result_by_id,
                baseline_row_by_id=baseline_row_by_id,
                fact_case_by_id=fact_case_by_id,
                fact_result_by_id=fact_result_by_id,
                cheap_first_gate=cheap_first_gate,
            )
            for need in radar["needs"]
        ]
        high_priority_rows = [row for row in evidence_rows if row["priority_band"] == "high"]
        blocked_rows = [row for row in evidence_rows if row["evidence_status"] == "blocked"]
        review_rows = [row for row in evidence_rows if row["evidence_status"] == "review_required"]
        not_run_rows = [row for row in evidence_rows if row["evidence_status"] == "not_run"]
        ready_rows = [row for row in evidence_rows if row["evidence_status"] == "ready"]
        high_priority_blocked_rows = [row for row in high_priority_rows if row["evidence_status"] == "blocked"]
        status = self._status(blocked_rows, high_priority_blocked_rows, review_rows, not_run_rows)

        return {
            "status": status,
            "method": {
                "type": "user-need-legal-document-benchmark-evidence",
                "notes": [
                    "Joins roadmap user-need IDs to local synthetic legal-document benchmark cases, fact consistency checks, local rule baseline, and cheap-first default evidence.",
                    "Treats not-run document or fact evaluations as evidence gaps; they do not imply production quality or public benchmark scores.",
                    "Returns IDs, counts, statuses, and validation commands only; no legal snippets, prompts, model outputs, payload bodies, or credentials are returned.",
                ],
            },
            "summary": {
                "need_count": len(evidence_rows),
                "high_priority_need_count": len(high_priority_rows),
                "ready_need_count": len(ready_rows),
                "review_required_need_count": len(review_rows),
                "blocked_need_count": len(blocked_rows),
                "not_run_need_count": len(not_run_rows),
                "high_priority_blocked_need_count": len(high_priority_blocked_rows),
                "document_fixture_case_count": len(document_case_by_id),
                "document_coverage_status": document_coverage["status"],
                "document_coverage_missing_type_count": document_coverage["summary"]["missing_document_type_count"],
                "document_evaluation_status": document_evaluation["status"],
                "document_evaluation_score": document_evaluation["score"],
                "document_evaluation_not_run_case_count": document_evaluation["not_run_case_count"],
                "fact_consistency_status": fact_evaluation["status"],
                "fact_consistency_score": fact_evaluation["score"],
                "fact_consistency_not_run_case_count": fact_evaluation["not_run_case_count"],
                "local_rule_baseline_status": local_rule_baseline["status"],
                "local_rule_baseline_score": local_rule_baseline["score"],
                "cheap_first_gate_status": cheap_first_gate["status"],
                "cheap_first_default_change_allowed": cheap_first_gate["summary"]["default_change_evidence_allowed"],
                "raw_payload_returned": False,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "evidence_rows": evidence_rows,
            "ready_need_ids": [row["need_id"] for row in ready_rows],
            "blocked_need_ids": [row["need_id"] for row in blocked_rows],
            "review_required_need_ids": [row["need_id"] for row in review_rows],
            "not_run_need_ids": [row["need_id"] for row in not_run_rows],
            "high_priority_blocked_need_ids": [row["need_id"] for row in high_priority_blocked_rows],
            "source_summaries": {
                "user_need_benchmark_coverage": user_need_coverage["summary"],
                "document_coverage": document_coverage["summary"],
                "document_evaluation": {
                    "status": document_evaluation["status"],
                    "score": document_evaluation["score"],
                    "case_count": document_evaluation["case_count"],
                    "blocking_case_ids": document_evaluation["blocking_case_ids"],
                },
                "fact_consistency": {
                    "status": fact_evaluation["status"],
                    "score": fact_evaluation["score"],
                    "case_count": fact_evaluation["case_count"],
                    "blocking_case_ids": fact_evaluation["blocking_case_ids"],
                },
                "local_rule_baseline": local_rule_baseline["summary"],
                "cheap_first_gate": cheap_first_gate["summary"],
            },
            "recommended_actions": self._recommended_actions(
                blocked_rows,
                high_priority_blocked_rows,
                review_rows,
                not_run_rows,
                document_coverage,
                document_evaluation,
                fact_evaluation,
                cheap_first_gate,
            ),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_user_feedback_text": False,
                "returns_document_snippets": False,
                "returns_fixture_snippets": False,
                "returns_public_benchmark_text": False,
                "returns_raw_candidate_text": False,
                "returns_raw_model_output": False,
                "returns_prompt_text": False,
                "returns_payload_bodies": False,
                "returns_credentials": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_called": False,
            },
            "claim_boundary": {
                "production_quality_claimed": False,
                "public_benchmark_score_claimed": False,
                "client_document_coverage_claimed": False,
                "default_model_changed": False,
                "allowed_claim": (
                    "The repository maps user needs to metadata-only local legal-document benchmark "
                    "evidence and cheap-first gate readiness."
                ),
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_user_need_legal_document_benchmark_evidence.py -q",
                "cd app/backend && python -m pytest tests/test_user_need_benchmark_coverage.py tests/test_legal_document_benchmark_suite.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_document_benchmark_fixtures.py tests/test_legal_document_fact_consistency_benchmark.py tests/test_modelops_legal_fixture_cheap_first_benchmark_gate.py -q",
            ],
        }

    def _evidence_row(
        self,
        *,
        need: dict[str, Any],
        coverage_row: dict[str, Any],
        document_case_by_id: dict[str, dict[str, Any]],
        document_coverage_by_id: dict[str, dict[str, Any]],
        document_result_by_id: dict[str, dict[str, Any]],
        baseline_row_by_id: dict[str, dict[str, Any]],
        fact_case_by_id: dict[str, dict[str, Any]],
        fact_result_by_id: dict[str, dict[str, Any]],
        cheap_first_gate: dict[str, Any],
    ) -> dict[str, Any]:
        need_id = str(need["id"])
        linked_document_case_ids = [
            case_id
            for case_id in self._strings(coverage_row.get("linked_document_fixture_ids"))
            if case_id in document_case_by_id
        ]
        public_document_case_ids = [
            case_id
            for case_id in self._strings(coverage_row.get("linked_public_document_fixture_ids"))
            if case_id in document_case_by_id
        ]
        all_document_case_ids = sorted(set(linked_document_case_ids) | set(public_document_case_ids))
        linked_fact_case_ids = self._linked_fact_case_ids(all_document_case_ids, fact_case_by_id)
        document_statuses = {
            case_id: str(document_result_by_id.get(case_id, {}).get("status") or "not_run")
            for case_id in all_document_case_ids
        }
        fact_statuses = {
            case_id: str(fact_result_by_id.get(case_id, {}).get("status") or "not_run")
            for case_id in linked_fact_case_ids
        }
        baseline_statuses = {
            case_id: str(baseline_row_by_id.get(case_id, {}).get("status") or "not_mapped")
            for case_id in all_document_case_ids
        }
        evidence_status = self._evidence_status(
            all_document_case_ids=all_document_case_ids,
            linked_fact_case_ids=linked_fact_case_ids,
            document_statuses=document_statuses,
            fact_statuses=fact_statuses,
            baseline_statuses=baseline_statuses,
            cheap_first_gate=cheap_first_gate,
        )
        reason_codes = self._reason_codes(
            all_document_case_ids=all_document_case_ids,
            linked_fact_case_ids=linked_fact_case_ids,
            document_statuses=document_statuses,
            fact_statuses=fact_statuses,
            baseline_statuses=baseline_statuses,
            cheap_first_gate=cheap_first_gate,
            evidence_status=evidence_status,
        )
        return {
            "need_id": need_id,
            "title": need["title"],
            "category": need["category"],
            "priority_band": need["priority_band"],
            "priority_score": need["priority_score"],
            "evidence_status": evidence_status,
            "coverage_status": coverage_row.get("coverage_status", "gap"),
            "document_case_ids": all_document_case_ids,
            "document_type_ids": self._document_type_ids(all_document_case_ids, document_case_by_id),
            "document_coverage_axes": self._document_coverage_axes(all_document_case_ids, document_coverage_by_id),
            "document_result_statuses": document_statuses,
            "fact_consistency_case_ids": linked_fact_case_ids,
            "fact_consistency_statuses": fact_statuses,
            "local_rule_baseline_statuses": baseline_statuses,
            "linked_public_source_ids": self._strings(coverage_row.get("linked_public_source_ids")),
            "linked_calibration_task_ids": self._strings(coverage_row.get("linked_calibration_task_ids")),
            "cheap_first_gate_status": cheap_first_gate["status"],
            "cheap_first_default_change_allowed": cheap_first_gate["summary"]["default_change_evidence_allowed"],
            "release_gate_links": self._strings(need.get("release_gate_links")),
            "reason_codes": reason_codes,
            "next_actions": self._row_actions(
                need_id,
                evidence_status,
                all_document_case_ids,
                linked_fact_case_ids,
                cheap_first_gate,
            ),
            "privacy_boundary": {
                "raw_document_text_returned": False,
                "raw_candidate_text_returned": False,
                "raw_model_output_returned": False,
                "payload_returned": False,
            },
        }

    def _evidence_status(
        self,
        *,
        all_document_case_ids: list[str],
        linked_fact_case_ids: list[str],
        document_statuses: dict[str, str],
        fact_statuses: dict[str, str],
        baseline_statuses: dict[str, str],
        cheap_first_gate: dict[str, Any],
    ) -> str:
        if not all_document_case_ids:
            return "blocked"
        if any(status == "fail" for status in document_statuses.values()):
            return "blocked"
        if any(status == "fail" for status in fact_statuses.values()):
            return "blocked"
        if any(status == "fail" for status in baseline_statuses.values()):
            return "blocked"
        if not linked_fact_case_ids:
            return "review_required"
        if any(status == "not_run" for status in document_statuses.values()):
            return "not_run"
        if any(status == "not_run" for status in fact_statuses.values()):
            return "not_run"
        if cheap_first_gate["status"] in {"blocked", "fail"}:
            return "blocked"
        if not cheap_first_gate["summary"]["default_change_evidence_allowed"]:
            return "review_required"
        combined_statuses = list(document_statuses.values()) + list(fact_statuses.values())
        if any(status in {"warn", "review_required"} for status in combined_statuses):
            return "review_required"
        return "ready"

    def _reason_codes(
        self,
        *,
        all_document_case_ids: list[str],
        linked_fact_case_ids: list[str],
        document_statuses: dict[str, str],
        fact_statuses: dict[str, str],
        baseline_statuses: dict[str, str],
        cheap_first_gate: dict[str, Any],
        evidence_status: str,
    ) -> list[str]:
        codes: list[str] = []
        if not all_document_case_ids:
            codes.append("no-linked-legal-document-benchmark-case")
        if not linked_fact_case_ids:
            codes.append("no-linked-fact-consistency-case")
        if any(status == "not_run" for status in document_statuses.values()):
            codes.append("document-benchmark-not-run")
        if any(status == "not_run" for status in fact_statuses.values()):
            codes.append("fact-consistency-not-run")
        if any(status == "fail" for status in document_statuses.values()):
            codes.append("document-benchmark-failed")
        if any(status == "fail" for status in fact_statuses.values()):
            codes.append("fact-consistency-failed")
        if any(status == "fail" for status in baseline_statuses.values()):
            codes.append("local-rule-baseline-failed")
        if not cheap_first_gate["summary"]["default_change_evidence_allowed"]:
            codes.append("cheap-first-default-change-not-evidence-ready")
        if evidence_status == "ready":
            codes.append("user-need-document-evidence-ready")
        return codes or ["user-need-document-evidence-review"]

    def _linked_fact_case_ids(
        self,
        document_case_ids: list[str],
        fact_case_by_id: dict[str, dict[str, Any]],
    ) -> list[str]:
        document_types = {
            self._document_type_from_case_id(case_id)
            for case_id in document_case_ids
        }
        linked = [
            case_id
            for case_id, case in fact_case_by_id.items()
            if str(case.get("document_type") or "") in document_types
        ]
        return sorted(linked)

    def _document_type_from_case_id(self, case_id: str) -> str:
        if case_id.startswith("ldoc-") and case_id.endswith("-mini"):
            return case_id.removeprefix("ldoc-").removesuffix("-mini").replace("-", "_")
        return ""

    def _document_type_ids(
        self,
        case_ids: list[str],
        document_case_by_id: dict[str, dict[str, Any]],
    ) -> list[str]:
        return sorted(
            {
                str(document_case_by_id[case_id].get("document_type") or "")
                for case_id in case_ids
                if case_id in document_case_by_id
            }
            - {""}
        )

    def _document_coverage_axes(
        self,
        case_ids: list[str],
        document_coverage_by_id: dict[str, dict[str, Any]],
    ) -> dict[str, int]:
        rows = [document_coverage_by_id[case_id] for case_id in case_ids if case_id in document_coverage_by_id]
        return {
            "required_section_count": sum(int(row.get("required_section_count") or 0) for row in rows),
            "expected_citation_count": sum(int(row.get("expected_citation_count") or 0) for row in rows),
            "expected_risk_label_count": sum(int(row.get("expected_risk_label_count") or 0) for row in rows),
            "banned_pii_category_count": sum(int(row.get("banned_pii_category_count") or 0) for row in rows),
        }

    def _row_actions(
        self,
        need_id: str,
        evidence_status: str,
        document_case_ids: list[str],
        fact_case_ids: list[str],
        cheap_first_gate: dict[str, Any],
    ) -> list[str]:
        if not document_case_ids:
            return [
                f"Add or link a synthetic legal-document benchmark case for user need {need_id}.",
                "Keep any public benchmark mapping metadata-only until license review passes.",
            ]
        if evidence_status == "not_run":
            return [
                "Run the local legal-document benchmark and fact consistency payload checks before release claims.",
                "Use laptop-safe synthetic fixtures only; do not import client documents or public benchmark rows.",
            ]
        if not fact_case_ids:
            return [
                "Add a fact consistency case for the mapped document types before default-model promotion.",
                "Keep current cheap-first defaults until fact consistency coverage is linked.",
            ]
        if not cheap_first_gate["summary"]["default_change_evidence_allowed"]:
            return [
                "Keep current cheap-first defaults until fixture, document, fact consistency, and calibration gates pass.",
                "Attach this need to the cheap-first release decision before changing model defaults.",
            ]
        return ["Evidence is ready; keep validation commands attached to the release packet."]

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        high_priority_blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        not_run_rows: list[dict[str, Any]],
        document_coverage: dict[str, Any],
        document_evaluation: dict[str, Any],
        fact_evaluation: dict[str, Any],
        cheap_first_gate: dict[str, Any],
    ) -> list[str]:
        if high_priority_blocked_rows:
            return [
                "Do not claim high-priority user needs have legal-document benchmark evidence until blockers are cleared: "
                + ", ".join(row["need_id"] for row in high_priority_blocked_rows[:6])
                + ".",
                "Add synthetic document/fact fixtures first; keep public benchmark and client documents out of laptop runs.",
                "Keep cheap-first default changes blocked until linked user needs pass document, fact, baseline, and calibration evidence.",
            ]
        if blocked_rows:
            return [
                "Clear blocked user-need document evidence rows before broad product coverage claims.",
                "Prioritize missing local document/fact fixture links over adding public benchmark examples.",
            ]
        if document_evaluation["status"] == "not_run" or fact_evaluation["status"] == "not_run":
            return [
                "Run document benchmark outputs and fact consistency outputs before claiming release-quality legal document generation.",
                "Use local rule baseline as smoke evidence only; it is not a production quality claim.",
            ]
        if review_rows or not_run_rows:
            return [
                "Review partial user-need evidence rows and rerun this bridge after benchmark payload checks.",
                "Keep current cheap-first defaults unless the legal fixture benchmark gate allows default-change evidence.",
            ]
        if document_coverage["status"] != "ready":
            return ["Add missing legal-document fixture types before broad coverage claims."]
        if not cheap_first_gate["summary"]["default_change_evidence_allowed"]:
            return ["Keep current cheap-first defaults until the legal fixture benchmark gate is fully ready."]
        return ["All user needs have metadata-level legal document benchmark evidence for release review."]

    def _status(
        self,
        blocked_rows: list[dict[str, Any]],
        high_priority_blocked_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        not_run_rows: list[dict[str, Any]],
    ) -> str:
        if high_priority_blocked_rows:
            return "blocked"
        if blocked_rows:
            return "ready_with_blockers"
        if review_rows:
            return "ready_with_review"
        if not_run_rows:
            return "ready_with_not_run_evidence"
        return "ready"

    def _cheap_first_payload(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        gate_payload = payload.get("cheap_first_gate")
        return gate_payload if isinstance(gate_payload, dict) else None

    def _safe_mapping(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def _strings(self, value: Any) -> list[str]:
        if not isinstance(value, list | tuple | set):
            return []
        return sorted({str(item) for item in value if str(item).strip()})
