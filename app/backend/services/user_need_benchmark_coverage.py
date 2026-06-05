from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_research_backlog import LegalResearchBacklogService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.user_needs_radar import UserNeedsRadarService


BENCHMARK_CASE_HINTS: dict[str, tuple[str, ...]] = {
    "traceable-legal-review": ("lease-dispute-evidence", "legal-rag-grounding", "service-contract-risk"),
    "cheap-first-review-routing": ("service-contract-risk", "privacy-sensitive-upload", "instruction-injection-upload"),
    "privacy-safe-upload": ("privacy-sensitive-upload", "instruction-injection-upload"),
    "robust-extraction-quality": ("long-pdf-extraction",),
    "prompt-injection-resilience": ("instruction-injection-upload",),
    "plain-language-actionability": ("service-contract-risk", "lease-dispute-evidence"),
}

DOCUMENT_CASE_HINTS: dict[str, tuple[str, ...]] = {
    "traceable-legal-review": (
        "ldoc-civil-complaint-mini",
        "ldoc-lawyer-letter-mini",
        "ldoc-contract-review-mini",
        "ldoc-evidence-catalog-mini",
        "ldoc-legal-opinion-mini",
    ),
    "privacy-safe-upload": (
        "ldoc-civil-complaint-mini",
        "ldoc-lawyer-letter-mini",
        "ldoc-contract-review-mini",
        "ldoc-evidence-catalog-mini",
        "ldoc-settlement-agreement-mini",
        "ldoc-legal-opinion-mini",
    ),
    "robust-extraction-quality": ("ldoc-contract-review-mini", "ldoc-evidence-catalog-mini"),
    "plain-language-actionability": (
        "ldoc-civil-complaint-mini",
        "ldoc-lawyer-letter-mini",
        "ldoc-evidence-catalog-mini",
        "ldoc-settlement-agreement-mini",
        "ldoc-legal-opinion-mini",
    ),
}


class UserNeedBenchmarkCoverageService:
    """Map user needs to local benchmark and fixture evidence without raw samples."""

    def __init__(
        self,
        user_needs_service: UserNeedsRadarService | None = None,
        benchmark_service: LegalReviewBenchmarkService | None = None,
        document_coverage_service: LegalDocumentBenchmarkCoverageService | None = None,
        backlog_service: LegalResearchBacklogService | None = None,
    ) -> None:
        self.user_needs_service = user_needs_service or UserNeedsRadarService()
        self.benchmark_service = benchmark_service or LegalReviewBenchmarkService()
        self.document_coverage_service = document_coverage_service or LegalDocumentBenchmarkCoverageService()
        self.backlog_service = backlog_service or LegalResearchBacklogService()

    def build_coverage(self) -> dict[str, Any]:
        radar = self.user_needs_service.build_radar()
        benchmark = self.benchmark_service.build_suite()
        document_coverage = self.document_coverage_service.build_matrix()
        backlog = self.backlog_service.build_backlog()
        rows = [
            self._coverage_row(need, benchmark, document_coverage, backlog)
            for need in radar["needs"]
        ]
        high_priority_rows = [row for row in rows if row["priority_band"] == "high"]
        gap_rows = [row for row in rows if row["coverage_status"] == "gap"]
        high_priority_gaps = [row for row in high_priority_rows if row["coverage_status"] == "gap"]
        status = "ready_with_gaps" if high_priority_gaps else "ready"

        return {
            "status": status,
            "method": {
                "type": "user-need-to-local-benchmark-coverage",
                "notes": [
                    "Links deterministic user-need IDs to local synthetic benchmark cases, fixture IDs, and research backlog items.",
                    "Reports planning coverage only; it is not a claim of production accuracy, public benchmark scores, or real client-document testing.",
                    "Uses explicit ID maps and release-gate intersections rather than raw text or model calls.",
                ],
            },
            "summary": {
                "need_count": len(rows),
                "high_priority_need_count": len(high_priority_rows),
                "covered_need_count": sum(1 for row in rows if row["coverage_status"] == "covered"),
                "partial_need_count": sum(1 for row in rows if row["coverage_status"] == "partial"),
                "gap_need_count": len(gap_rows),
                "high_priority_gap_count": len(high_priority_gaps),
                "benchmark_case_count": benchmark["case_count"],
                "synthetic_fixture_count": benchmark["document_fixture_count"],
                "document_fixture_count": document_coverage["summary"]["case_count"],
                "research_backlog_item_count": backlog["summary"]["backlog_item_count"],
                "local_run_only": True,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "coverage_rows": rows,
            "gap_need_ids": [row["need_id"] for row in gap_rows],
            "high_priority_gap_need_ids": [row["need_id"] for row in high_priority_gaps],
            "recommended_actions": self._recommended_actions(rows, high_priority_gaps),
            "privacy_boundary": {
                "returns_fixture_snippets": False,
                "returns_raw_benchmark_samples": False,
                "returns_raw_model_output": False,
                "returns_user_feedback_text": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "source": "metadata_only_local_services",
            },
            "validation_commands": [
                "python -m pytest tests/test_user_need_benchmark_coverage.py -q",
                "python -m pytest tests/test_user_needs_radar.py tests/test_legal_review_benchmark.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_research_backlog.py -q",
            ],
        }

    def _coverage_row(
        self,
        need: dict[str, Any],
        benchmark: dict[str, Any],
        document_coverage: dict[str, Any],
        backlog: dict[str, Any],
    ) -> dict[str, Any]:
        need_id = str(need["id"])
        linked_case_ids = self._linked_benchmark_case_ids(need, benchmark)
        linked_fixture_ids = self._linked_fixture_ids(linked_case_ids, benchmark)
        linked_document_fixture_ids = self._linked_document_fixture_ids(need_id, document_coverage)
        linked_backlog_item_ids = [
            item["id"]
            for item in backlog["backlog"]
            if need_id in item["user_need_ids"]
        ]
        linked_release_gates = sorted(
            set(need["release_gate_links"])
            | {
                gate
                for case in benchmark["cases"]
                if case["id"] in linked_case_ids
                for gate in case["release_gate_links"]
            }
            | {
                gate
                for item in backlog["backlog"]
                if item["id"] in linked_backlog_item_ids
                for gate in item["release_gate_links"]
            }
        )
        coverage_status = self._coverage_status(
            linked_case_ids,
            linked_fixture_ids,
            linked_document_fixture_ids,
            linked_backlog_item_ids,
        )
        return {
            "need_id": need_id,
            "title": need["title"],
            "category": need["category"],
            "priority_band": need["priority_band"],
            "priority_score": need["priority_score"],
            "linked_benchmark_case_ids": linked_case_ids,
            "linked_fixture_ids": linked_fixture_ids,
            "linked_document_fixture_ids": linked_document_fixture_ids,
            "linked_backlog_item_ids": linked_backlog_item_ids,
            "linked_release_gates": linked_release_gates,
            "coverage_status": coverage_status,
            "gap_reasons": self._gap_reasons(coverage_status, linked_case_ids, linked_fixture_ids, linked_backlog_item_ids),
            "next_actions": self._next_actions(need, coverage_status, linked_case_ids, linked_document_fixture_ids),
        }

    def _linked_benchmark_case_ids(self, need: dict[str, Any], benchmark: dict[str, Any]) -> list[str]:
        hinted = set(BENCHMARK_CASE_HINTS.get(str(need["id"]), ()))
        need_gates = set(need["release_gate_links"])
        linked = [
            case["id"]
            for case in benchmark["cases"]
            if case["id"] in hinted or need_gates.intersection(case["release_gate_links"])
        ]
        return sorted(set(linked))

    def _linked_fixture_ids(self, case_ids: list[str], benchmark: dict[str, Any]) -> list[str]:
        case_id_set = set(case_ids)
        return sorted(
            fixture["id"]
            for fixture in benchmark["document_fixtures"]
            if case_id_set.intersection(fixture["linked_case_ids"])
        )

    def _linked_document_fixture_ids(self, need_id: str, document_coverage: dict[str, Any]) -> list[str]:
        hinted = set(DOCUMENT_CASE_HINTS.get(need_id, ()))
        available = {row["case_id"] for row in document_coverage["case_rows"]}
        return sorted(hinted.intersection(available))

    def _coverage_status(
        self,
        linked_case_ids: list[str],
        linked_fixture_ids: list[str],
        linked_document_fixture_ids: list[str],
        linked_backlog_item_ids: list[str],
    ) -> str:
        if linked_case_ids and linked_fixture_ids and linked_backlog_item_ids:
            return "covered"
        if linked_case_ids or linked_fixture_ids or linked_document_fixture_ids or linked_backlog_item_ids:
            return "partial"
        return "gap"

    def _gap_reasons(
        self,
        status: str,
        linked_case_ids: list[str],
        linked_fixture_ids: list[str],
        linked_backlog_item_ids: list[str],
    ) -> list[str]:
        reasons: list[str] = []
        if not linked_case_ids:
            reasons.append("no_linked_benchmark_case")
        if not linked_fixture_ids:
            reasons.append("no_linked_synthetic_fixture")
        if not linked_backlog_item_ids:
            reasons.append("no_linked_research_backlog_item")
        if status == "covered":
            reasons.append("metadata_coverage_present")
        return reasons

    def _next_actions(
        self,
        need: dict[str, Any],
        status: str,
        linked_case_ids: list[str],
        linked_document_fixture_ids: list[str],
    ) -> list[str]:
        if status == "covered":
            return [
                f"Keep local benchmark cases attached before changing {need['id']}: {', '.join(linked_case_ids[:4])}.",
                "Run the quick suite and fixture regression comparator after prompt, routing, or report-schema changes.",
            ]
        actions = [
            f"Add or link a laptop-safe synthetic fixture for user need {need['id']}.",
            "Attach a research backlog item and validation command before making public coverage claims.",
        ]
        if linked_document_fixture_ids:
            actions.append("Promote linked legal-document fixtures into a focused run plan before release review.")
        return actions[:3]

    def _recommended_actions(self, rows: list[dict[str, Any]], high_priority_gaps: list[dict[str, Any]]) -> list[str]:
        if high_priority_gaps:
            return [
                "Do not claim high-priority user needs have benchmark coverage until these gaps are linked: "
                + ", ".join(row["need_id"] for row in high_priority_gaps[:6])
                + ".",
                "Add synthetic local fixtures first; keep public benchmark raw examples out of default laptop runs.",
                "Rebuild this map after adding benchmark cases, document fixtures, or research backlog links.",
            ]
        partial = [row for row in rows if row["coverage_status"] == "partial"]
        if partial:
            return [
                "High-priority user needs have local benchmark links; review partial medium/low needs before broad claims.",
                "Use fixture regression comparison before promoting cheap-first or prompt changes.",
            ]
        return ["All user needs have metadata-level local benchmark coverage; keep validation evidence attached to release readiness."]
