from __future__ import annotations

from typing import Any

from services.gemini_newapi_cheap_first_calibration import GeminiNewapiCheapFirstCalibrationService
from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
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
        public_sampler_service: LegalPublicBenchmarkSamplerService | None = None,
        cheap_first_calibration_service: GeminiNewapiCheapFirstCalibrationService | None = None,
        backlog_service: LegalResearchBacklogService | None = None,
    ) -> None:
        self.user_needs_service = user_needs_service or UserNeedsRadarService()
        self.benchmark_service = benchmark_service or LegalReviewBenchmarkService()
        self.document_coverage_service = document_coverage_service or LegalDocumentBenchmarkCoverageService()
        self.public_sampler_service = public_sampler_service or LegalPublicBenchmarkSamplerService()
        self.cheap_first_calibration_service = (
            cheap_first_calibration_service or GeminiNewapiCheapFirstCalibrationService()
        )
        self.backlog_service = backlog_service or LegalResearchBacklogService()

    def build_coverage(self) -> dict[str, Any]:
        radar = self.user_needs_service.build_radar()
        benchmark = self.benchmark_service.build_suite()
        document_coverage = self.document_coverage_service.build_matrix()
        public_sampler = self.public_sampler_service.build_plan()
        cheap_first_calibration = self.cheap_first_calibration_service.build_calibration()
        backlog = self.backlog_service.build_backlog()
        rows = [
            self._coverage_row(need, benchmark, document_coverage, public_sampler, cheap_first_calibration, backlog)
            for need in radar["needs"]
        ]
        high_priority_rows = [row for row in rows if row["priority_band"] == "high"]
        gap_rows = [row for row in rows if row["coverage_status"] == "gap"]
        high_priority_gaps = [row for row in high_priority_rows if row["coverage_status"] == "gap"]
        public_source_plans = public_sampler.get("source_plans", [])
        ready_public_sources = [item for item in public_source_plans if item["sampling_state"] == "sampling_ready"]
        license_review_sources = [
            item for item in public_source_plans if item["sampling_state"] == "license_review_required"
        ]
        catalog_only_sources = [item for item in public_source_plans if item["sampling_state"] == "catalog_only"]
        public_mapped_rows = [row for row in rows if row["linked_public_source_ids"]]
        public_ready_rows = [row for row in rows if row["public_benchmark_status"] == "sampling_ready"]
        public_license_rows = [row for row in rows if row["public_benchmark_status"] == "license_review_required"]
        public_document_rows = [row for row in rows if row["linked_public_document_fixture_ids"]]
        calibration_mapped_rows = [row for row in rows if row["linked_calibration_task_ids"]]
        calibration_pass_rows = [row for row in rows if row["calibration_status"] == "pass"]
        calibration_attention_rows = [
            row for row in rows if row["calibration_status"] in {"warn", "fail"}
        ]
        status = "ready_with_gaps" if high_priority_gaps else "ready"

        return {
            "status": status,
            "method": {
                "type": "user-need-to-local-benchmark-coverage",
                "notes": [
                    "Links deterministic user-need IDs to local synthetic benchmark cases, fixture IDs, and research backlog items.",
                    "Reports planning coverage only; it is not a claim of production accuracy, public benchmark scores, or real client-document testing.",
                    "Uses explicit ID maps and release-gate intersections rather than raw text or model calls.",
                    "Joins the public benchmark sampler so user needs show LegalBench, CUAD, LexGLUE, LegalBench-RAG, LexEval, CaseGen, and Pile of Law readiness without downloading datasets.",
                    "Joins cheap-first Gemini/NewAPI calibration tasks by user_need_ids so model-routing evidence is visible in the same coverage map.",
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
                "public_benchmark_source_count": len(public_source_plans),
                "public_benchmark_ready_source_count": len(ready_public_sources),
                "public_benchmark_license_review_required_source_count": len(license_review_sources),
                "public_benchmark_catalog_only_source_count": len(catalog_only_sources),
                "public_benchmark_mapped_need_count": len(public_mapped_rows),
                "public_benchmark_ready_need_count": len(public_ready_rows),
                "public_benchmark_license_review_required_need_count": len(public_license_rows),
                "public_benchmark_document_fixture_mapped_need_count": len(public_document_rows),
                "public_sampler_endpoint": "/api/v1/maintenance/legal-review-benchmark/public-sampler",
                "public_sampler_network_access": public_sampler["resource_policy"]["network_access"],
                "cheap_first_calibration_status": cheap_first_calibration["status"],
                "cheap_first_calibration_task_count": cheap_first_calibration["summary"]["task_count"],
                "cheap_first_calibration_mapped_need_count": len(calibration_mapped_rows),
                "cheap_first_calibration_pass_need_count": len(calibration_pass_rows),
                "cheap_first_calibration_attention_need_count": len(calibration_attention_rows),
                "local_run_only": True,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "coverage_rows": rows,
            "gap_need_ids": [row["need_id"] for row in gap_rows],
            "high_priority_gap_need_ids": [row["need_id"] for row in high_priority_gaps],
            "public_benchmark_gap_need_ids": [row["need_id"] for row in public_license_rows],
            "calibration_attention_need_ids": [row["need_id"] for row in calibration_attention_rows],
            "source_summaries": {
                "public_sampler": public_sampler["summary"],
                "public_sampler_resource_policy": public_sampler["resource_policy"],
                "cheap_first_calibration": cheap_first_calibration["summary"],
            },
            "recommended_actions": self._recommended_actions(rows, high_priority_gaps),
            "privacy_boundary": {
                "returns_fixture_snippets": False,
                "returns_raw_benchmark_samples": False,
                "returns_public_benchmark_text": False,
                "returns_raw_model_output": False,
                "returns_calibration_payloads": False,
                "returns_user_feedback_text": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "source": "metadata_only_local_services",
            },
            "validation_commands": [
                "python -m pytest tests/test_user_need_benchmark_coverage.py -q",
                "python -m pytest tests/test_user_needs_radar.py tests/test_legal_review_benchmark.py tests/test_legal_document_benchmark_coverage.py tests/test_legal_public_benchmark_sampler.py tests/test_gemini_newapi_cheap_first_calibration.py tests/test_legal_research_backlog.py -q",
            ],
        }

    def _coverage_row(
        self,
        need: dict[str, Any],
        benchmark: dict[str, Any],
        document_coverage: dict[str, Any],
        public_sampler: dict[str, Any],
        cheap_first_calibration: dict[str, Any],
        backlog: dict[str, Any],
    ) -> dict[str, Any]:
        need_id = str(need["id"])
        linked_case_ids = self._linked_benchmark_case_ids(need, benchmark)
        linked_fixture_ids = self._linked_fixture_ids(linked_case_ids, benchmark)
        linked_document_fixture_ids = self._linked_document_fixture_ids(need_id, document_coverage)
        linked_public_source_ids = self._linked_public_source_ids(
            need,
            linked_case_ids,
            linked_fixture_ids,
            linked_document_fixture_ids,
            public_sampler,
        )
        public_sampling_states = self._public_sampling_states(linked_public_source_ids, public_sampler)
        linked_public_sampling_batch_ids = self._linked_public_sampling_batch_ids(
            linked_public_source_ids,
            linked_fixture_ids,
            public_sampler,
        )
        linked_calibration_rows = self._linked_calibration_rows(need_id, cheap_first_calibration)
        linked_calibration_task_ids = [row["id"] for row in linked_calibration_rows]
        linked_calibration_release_gates = sorted(
            {
                gate
                for row in linked_calibration_rows
                for gate in row.get("release_gate_links", [])
            }
        )
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
            "linked_public_source_ids": linked_public_source_ids,
            "linked_public_document_fixture_ids": self._linked_public_document_fixture_ids(
                linked_public_source_ids,
                public_sampler,
            ),
            "linked_public_sampling_batch_ids": linked_public_sampling_batch_ids,
            "public_sampling_states": public_sampling_states,
            "public_benchmark_status": self._public_benchmark_status(public_sampling_states),
            "linked_calibration_task_ids": linked_calibration_task_ids,
            "linked_calibration_release_gates": linked_calibration_release_gates,
            "calibration_status": self._calibration_status(linked_calibration_rows),
            "calibration_decisions": {
                row["id"]: str(row.get("calibration_decision") or "unknown")
                for row in linked_calibration_rows
            },
            "linked_backlog_item_ids": linked_backlog_item_ids,
            "linked_release_gates": linked_release_gates,
            "coverage_status": coverage_status,
            "gap_reasons": self._gap_reasons(
                coverage_status,
                linked_case_ids,
                linked_fixture_ids,
                linked_backlog_item_ids,
                public_sampling_states,
                linked_calibration_rows,
            ),
            "next_actions": self._next_actions(
                need,
                coverage_status,
                linked_case_ids,
                linked_document_fixture_ids,
                public_sampling_states,
                linked_calibration_rows,
            ),
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

    def _linked_public_source_ids(
        self,
        need: dict[str, Any],
        linked_case_ids: list[str],
        linked_fixture_ids: list[str],
        linked_document_fixture_ids: list[str],
        public_sampler: dict[str, Any],
    ) -> list[str]:
        need_source_ids = {str(source_id) for source_id in need.get("source_ids", [])}
        case_ids = set(linked_case_ids)
        fixture_ids = set(linked_fixture_ids)
        document_fixture_ids = set(linked_document_fixture_ids)
        linked: set[str] = set()
        for plan in public_sampler.get("source_plans", []):
            source_id = str(plan.get("source_id") or "")
            if not source_id:
                continue
            plan_cases = {str(item) for item in plan.get("benchmark_case_ids", [])}
            plan_fixtures = {str(item) for item in plan.get("local_fixture_ids", [])}
            plan_document_fixtures = {str(item) for item in plan.get("document_fixture_ids", [])}
            if (
                source_id in need_source_ids
                or case_ids.intersection(plan_cases)
                or fixture_ids.intersection(plan_fixtures)
                or document_fixture_ids.intersection(plan_document_fixtures)
            ):
                linked.add(source_id)
        return sorted(linked)

    def _linked_public_document_fixture_ids(
        self,
        linked_public_source_ids: list[str],
        public_sampler: dict[str, Any],
    ) -> list[str]:
        source_ids = set(linked_public_source_ids)
        document_fixture_ids = {
            str(item)
            for plan in public_sampler.get("source_plans", [])
            if str(plan.get("source_id") or "") in source_ids
            for item in plan.get("document_fixture_ids", [])
        }
        return sorted(document_fixture_ids)

    def _public_sampling_states(
        self,
        linked_public_source_ids: list[str],
        public_sampler: dict[str, Any],
    ) -> dict[str, str]:
        plans_by_id = {str(plan["source_id"]): plan for plan in public_sampler.get("source_plans", [])}
        return {
            source_id: str(plans_by_id[source_id].get("sampling_state") or "unknown")
            for source_id in linked_public_source_ids
            if source_id in plans_by_id
        }

    def _linked_public_sampling_batch_ids(
        self,
        linked_public_source_ids: list[str],
        linked_fixture_ids: list[str],
        public_sampler: dict[str, Any],
    ) -> list[str]:
        source_ids = set(linked_public_source_ids)
        fixture_ids = set(linked_fixture_ids)
        batch_ids = [
            str(batch["id"])
            for batch in public_sampler.get("sampling_batches", [])
            if source_ids.intersection(str(item) for item in batch.get("source_ids", []))
            or fixture_ids.intersection(str(item) for item in batch.get("local_fixture_ids", []))
        ]
        return sorted(set(batch_ids))

    def _public_benchmark_status(self, public_sampling_states: dict[str, str]) -> str:
        states = set(public_sampling_states.values())
        if not states:
            return "not_mapped"
        if "sampling_ready" in states:
            return "sampling_ready"
        if "license_review_required" in states:
            return "license_review_required"
        if states == {"catalog_only"}:
            return "catalog_only"
        return "mapped"

    def _linked_calibration_rows(self, need_id: str, cheap_first_calibration: dict[str, Any]) -> list[dict[str, Any]]:
        task_ids = {
            str(task["id"])
            for task in cheap_first_calibration.get("calibration_tasks", [])
            if need_id in {str(item) for item in task.get("user_need_ids", [])}
        }
        return [
            row
            for row in cheap_first_calibration.get("calibration_rows", [])
            if str(row.get("id")) in task_ids
        ]

    def _calibration_status(self, linked_calibration_rows: list[dict[str, Any]]) -> str:
        statuses = {str(row.get("status") or "unknown") for row in linked_calibration_rows}
        if not statuses:
            return "not_mapped"
        if "fail" in statuses:
            return "fail"
        if "warn" in statuses:
            return "warn"
        if statuses == {"pass"}:
            return "pass"
        return "mapped"

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
        public_sampling_states: dict[str, str],
        linked_calibration_rows: list[dict[str, Any]],
    ) -> list[str]:
        reasons: list[str] = []
        if not linked_case_ids:
            reasons.append("no_linked_benchmark_case")
        if not linked_fixture_ids:
            reasons.append("no_linked_synthetic_fixture")
        if not linked_backlog_item_ids:
            reasons.append("no_linked_research_backlog_item")
        if "license_review_required" in public_sampling_states.values():
            reasons.append("public_benchmark_license_review_required")
        if public_sampling_states and set(public_sampling_states.values()) == {"catalog_only"}:
            reasons.append("public_benchmark_catalog_only")
        if linked_calibration_rows and self._calibration_status(linked_calibration_rows) in {"warn", "fail"}:
            reasons.append("cheap_first_calibration_attention_required")
        if status == "covered":
            reasons.append("metadata_coverage_present")
        return reasons

    def _next_actions(
        self,
        need: dict[str, Any],
        status: str,
        linked_case_ids: list[str],
        linked_document_fixture_ids: list[str],
        public_sampling_states: dict[str, str],
        linked_calibration_rows: list[dict[str, Any]],
    ) -> list[str]:
        if status == "covered":
            actions = [
                f"Keep local benchmark cases attached before changing {need['id']}: {', '.join(linked_case_ids[:4])}.",
                "Run the quick suite and fixture regression comparator after prompt, routing, or report-schema changes.",
            ]
            if "license_review_required" in public_sampling_states.values():
                actions.append("Complete public benchmark license review before importing any external examples.")
            if self._calibration_status(linked_calibration_rows) in {"warn", "fail"}:
                actions.append("Review cheap-first calibration warnings before changing Gemini/NewAPI defaults.")
            return actions[:3]
        actions = [
            f"Add or link a laptop-safe synthetic fixture for user need {need['id']}.",
            "Attach a research backlog item and validation command before making public coverage claims.",
        ]
        if linked_document_fixture_ids:
            actions.append("Promote linked legal-document fixtures into a focused run plan before release review.")
        if "license_review_required" in public_sampling_states.values():
            actions.append("Keep public benchmark mapping metadata-only until license and attribution review pass.")
        if self._calibration_status(linked_calibration_rows) in {"warn", "fail"}:
            actions.append("Attach passing cheap-first calibration rows before promoting model-routing claims.")
        return actions[:3]

    def _recommended_actions(self, rows: list[dict[str, Any]], high_priority_gaps: list[dict[str, Any]]) -> list[str]:
        public_license_rows = [row for row in rows if row["public_benchmark_status"] == "license_review_required"]
        calibration_attention_rows = [row for row in rows if row["calibration_status"] in {"warn", "fail"}]
        if high_priority_gaps:
            return [
                "Do not claim high-priority user needs have benchmark coverage until these gaps are linked: "
                + ", ".join(row["need_id"] for row in high_priority_gaps[:6])
                + ".",
                "Add synthetic local fixtures first; keep public benchmark raw examples out of default laptop runs.",
                "Rebuild this map after adding benchmark cases, document fixtures, or research backlog links.",
            ]
        if public_license_rows:
            return [
                "High-priority user needs have local benchmark links; keep public benchmark evidence metadata-only until license review passes for mapped sources.",
                "Use /api/v1/maintenance/legal-review-benchmark/public-sampler before importing LegalBench, CUAD, LexGLUE, LegalBench-RAG, LexEval, CaseGen, or corpus-scale samples.",
                "Use fixture regression comparison before promoting cheap-first or prompt changes.",
            ]
        if calibration_attention_rows:
            return [
                "Keep model-routing claims tied to user needs blocked until cheap-first calibration rows pass.",
                "Review selector replay, fixture reports, cost guardrails, and mapped user_need_ids before changing defaults.",
            ]
        partial = [row for row in rows if row["coverage_status"] == "partial"]
        if partial:
            return [
                "High-priority user needs have local benchmark links; review partial medium/low needs before broad claims.",
                "Use fixture regression comparison before promoting cheap-first or prompt changes.",
            ]
        return ["All user needs have metadata-level local benchmark coverage; keep validation evidence attached to release readiness."]
