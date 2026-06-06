from __future__ import annotations

from typing import Any

from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.legal_review_benchmark import LegalReviewBenchmarkService
from services.small_legal_document_corpus_expansion import SmallLegalDocumentCorpusExpansionService


class LegalBenchmarkFixtureCrosswalkService:
    """Join public benchmark sources to local fixture and corpus metadata only."""

    def build_crosswalk(self) -> dict[str, Any]:
        benchmark = LegalReviewBenchmarkService().build_suite()
        sampler = LegalPublicBenchmarkSamplerService().build_plan()
        document_coverage = LegalDocumentBenchmarkCoverageService().build_matrix()
        corpus = SmallLegalDocumentCorpusExpansionService().build_corpus()

        benchmark_cases = {case["id"]: self._benchmark_case_row(case) for case in benchmark["cases"]}
        local_fixtures = {
            fixture["id"]: self._local_fixture_row(fixture)
            for fixture in benchmark["document_fixtures"]
        }
        document_cases = {
            row["case_id"]: self._document_case_row(row)
            for row in document_coverage["case_rows"]
        }
        corpus_items = {
            item["id"]: self._corpus_item_row(item)
            for item in corpus["corpus_items"]
        }

        rows = [
            self._source_row(
                plan,
                benchmark_cases,
                local_fixtures,
                document_cases,
                corpus_items,
            )
            for plan in sampler["source_plans"]
        ]
        gap_queue = self._gap_queue(rows)

        return {
            "status": "ready",
            "method": {
                "type": "legal-benchmark-fixture-crosswalk",
                "purpose": (
                    "Map public legal benchmark source IDs to local benchmark cases, synthetic fixture IDs, "
                    "legal-document fixture IDs, and tiny corpus item IDs without importing public examples."
                ),
                "source_services": [
                    "legal_review_benchmark",
                    "legal_public_benchmark_sampler",
                    "legal_document_benchmark_coverage",
                    "small_legal_document_corpus_expansion",
                ],
                "claim_boundary": "This is mapping evidence only; it does not claim public benchmark scores or dataset coverage.",
            },
            "summary": {
                "source_count": len(rows),
                "source_with_benchmark_case_count": sum(1 for row in rows if row["benchmark_case_ids"]),
                "source_with_local_fixture_count": sum(1 for row in rows if row["local_fixture_ids"]),
                "source_with_document_fixture_count": sum(1 for row in rows if row["document_fixture_ids"]),
                "source_with_small_corpus_count": sum(1 for row in rows if row["small_corpus_item_ids"]),
                "gap_count": len(gap_queue),
                "public_benchmark_score_claimed": False,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "source_rows": rows,
            "gap_queue": gap_queue,
            "privacy_boundary": {
                "returns_public_benchmark_text": False,
                "returns_local_fixture_snippets": False,
                "returns_small_corpus_excerpts": False,
                "returns_generated_text": False,
                "returns_raw_model_output": False,
                "returns_credentials": False,
                "downloads_datasets": False,
                "model_calls": False,
            },
            "recommended_actions": self._recommended_actions(gap_queue),
            "validation_commands": [
                "python -m pytest tests/test_legal_benchmark_fixture_crosswalk.py -q",
                "python -m pytest tests/test_legal_public_benchmark_sampler.py tests/test_user_need_benchmark_coverage.py -q",
            ],
        }

    def _source_row(
        self,
        plan: dict[str, Any],
        benchmark_cases: dict[str, dict[str, Any]],
        local_fixtures: dict[str, dict[str, Any]],
        document_cases: dict[str, dict[str, Any]],
        corpus_items: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        local_fixture_ids = self._known_ids(plan.get("local_fixture_ids"), local_fixtures)
        document_fixture_ids = self._known_ids(plan.get("document_fixture_ids"), document_cases)
        benchmark_case_ids = self._known_ids(plan.get("benchmark_case_ids"), benchmark_cases)
        small_corpus_item_ids = self._small_corpus_item_ids(local_fixture_ids, document_fixture_ids, corpus_items)
        return {
            "source_id": plan["source_id"],
            "title": plan["title"],
            "priority": plan["priority"],
            "resource_profile": plan["resource_profile"],
            "sampling_state": plan["sampling_state"],
            "license_gate": plan["license_gate"],
            "validation_targets": list(plan["validation_targets"]),
            "benchmark_case_ids": benchmark_case_ids,
            "benchmark_case_rows": [benchmark_cases[item_id] for item_id in benchmark_case_ids],
            "local_fixture_ids": local_fixture_ids,
            "local_fixture_rows": [local_fixtures[item_id] for item_id in local_fixture_ids],
            "document_fixture_ids": document_fixture_ids,
            "document_fixture_rows": [document_cases[item_id] for item_id in document_fixture_ids],
            "small_corpus_item_ids": small_corpus_item_ids,
            "small_corpus_item_rows": [corpus_items[item_id] for item_id in small_corpus_item_ids],
            "coverage_status": self._coverage_status(
                local_fixture_ids=local_fixture_ids,
                document_fixture_ids=document_fixture_ids,
                small_corpus_item_ids=small_corpus_item_ids,
                sampling_state=str(plan["sampling_state"]),
            ),
        }

    def _known_ids(self, values: Any, known: dict[str, dict[str, Any]]) -> list[str]:
        if not isinstance(values, list):
            return []
        return [str(value) for value in values if str(value) in known]

    def _small_corpus_item_ids(
        self,
        local_fixture_ids: list[str],
        document_fixture_ids: list[str],
        corpus_items: dict[str, dict[str, Any]],
    ) -> list[str]:
        candidate_ids: set[str] = set()
        for fixture_id in local_fixture_ids:
            candidate_ids.update(LOCAL_FIXTURE_TO_CORPUS_ITEM_IDS.get(fixture_id, ()))
        for fixture_id in document_fixture_ids:
            candidate_ids.update(DOCUMENT_FIXTURE_TO_CORPUS_ITEM_IDS.get(fixture_id, ()))
        return sorted(item_id for item_id in candidate_ids if item_id in corpus_items)

    def _coverage_status(
        self,
        *,
        local_fixture_ids: list[str],
        document_fixture_ids: list[str],
        small_corpus_item_ids: list[str],
        sampling_state: str,
    ) -> str:
        if not local_fixture_ids:
            return "local_fixture_gap"
        if sampling_state == "catalog_only":
            return "catalog_reference_mapped"
        if not document_fixture_ids:
            return "ready_with_document_fixture_gap"
        if not small_corpus_item_ids:
            return "ready_with_corpus_gap"
        return "ready"

    def _gap_queue(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        queue: list[dict[str, Any]] = []
        for row in rows:
            reasons: list[str] = []
            if row["sampling_state"] == "license_review_required":
                reasons.append("license_review_required")
            if not row["document_fixture_ids"]:
                reasons.append("document_fixture_mapping_missing")
            if not row["small_corpus_item_ids"]:
                reasons.append("small_corpus_mapping_missing")
            if not reasons:
                continue
            queue.append(
                {
                    "source_id": row["source_id"],
                    "priority": "high" if row["priority"] == "high" else "medium",
                    "gap_reasons": reasons,
                    "recommended_action": self._gap_action(row, reasons),
                    "validation_target": "/api/v1/maintenance/legal-review-benchmark/fixture-crosswalk",
                }
            )
        return queue

    def _gap_action(self, row: dict[str, Any], reasons: list[str]) -> str:
        if "document_fixture_mapping_missing" in reasons:
            return f"Link {row['source_id']} to at least one ldoc-* fixture before using it in document-generation claims."
        if "small_corpus_mapping_missing" in reasons:
            return f"Add a tiny synthetic corpus metadata row for {row['source_id']} or mark the source catalog-only."
        return f"Complete source review before enabling any sampled {row['source_id']} observations."

    def _recommended_actions(self, gap_queue: list[dict[str, Any]]) -> list[str]:
        actions = [
            "Use this crosswalk before adding new public benchmark samples so every source has a local fixture path.",
            "Keep public benchmark text, local snippets, small-corpus excerpts, prompts, model outputs, and credentials out of this endpoint.",
        ]
        if gap_queue:
            actions.append("Close high-priority document-fixture and corpus mappings before claiming expanded legal coverage.")
        return actions

    def _benchmark_case_row(self, case: dict[str, Any]) -> dict[str, Any]:
        return {
            "case_id": case["id"],
            "title": case["title"],
            "matter_type": case["matter_type"],
            "task_family": case["task_family"],
            "user_segment": case["user_segment"],
            "expected_route": case["expected_route"],
            "required_metrics": list(case["required_metrics"]),
            "benchmark_sources": list(case["benchmark_sources"]),
            "release_gate_links": list(case["release_gate_links"]),
        }

    def _local_fixture_row(self, fixture: dict[str, Any]) -> dict[str, Any]:
        return {
            "fixture_id": fixture["id"],
            "title": fixture["title"],
            "matter_type": fixture["matter_type"],
            "linked_case_ids": list(fixture["linked_case_ids"]),
            "expected_task_count": len(fixture["expected_tasks"]),
            "expected_signal_count": len(fixture["expected_signals"]),
            "source_relation": fixture["source_relation"],
        }

    def _document_case_row(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "case_id": row["case_id"],
            "title": row["title"],
            "document_type": row["document_type"],
            "matter_type": row["matter_type"],
            "required_section_count": row["required_section_count"],
            "expected_citation_count": row["expected_citation_count"],
            "expected_risk_label_count": row["expected_risk_label_count"],
            "banned_pii_category_count": row["banned_pii_category_count"],
            "local_run_fit": row["local_run_fit"],
        }

    def _corpus_item_row(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "item_id": item["id"],
            "title": item["title"],
            "domain": item["domain"],
            "matter_type": item["matter_type"],
            "document_type": item["document_type"],
            "source_type": item["source_type"],
            "language": item["language"],
            "task_count": len(item["tasks"]),
            "risk_tag_count": len(item["risk_tags"]),
            "difficulty": item["difficulty"],
            "local_checks": list(item["local_checks"]),
        }


LOCAL_FIXTURE_TO_CORPUS_ITEM_IDS: dict[str, tuple[str, ...]] = {
    "fixture-service-agreement-small": ("small-corpus-service-004",),
    "fixture-lease-dispute-notice-small": ("small-corpus-lease-002",),
    "fixture-adversarial-upload-small": ("small-corpus-lending-005",),
    "fixture-low-text-pdf-page-small": (),
}


DOCUMENT_FIXTURE_TO_CORPUS_ITEM_IDS: dict[str, tuple[str, ...]] = {
    "ldoc-civil-complaint-mini": ("small-corpus-sales-003",),
    "ldoc-lawyer-letter-mini": ("small-corpus-lease-002",),
    "ldoc-contract-review-mini": ("small-corpus-service-004",),
    "ldoc-evidence-catalog-mini": ("small-corpus-labor-001",),
    "ldoc-settlement-agreement-mini": ("small-corpus-service-004",),
    "ldoc-legal-opinion-mini": ("small-corpus-service-004",),
}
