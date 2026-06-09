from __future__ import annotations

from typing import Any

from services.legal_benchmark_fixture_crosswalk import LegalBenchmarkFixtureCrosswalkService
from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.legal_document_benchmark_fixtures import LegalDocumentBenchmarkFixturesService
from services.legal_public_benchmark_sampler import LegalPublicBenchmarkSamplerService
from services.small_legal_document_corpus_expansion import SmallLegalDocumentCorpusExpansionService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService


CHINESE_LEGAL_SOURCE_IDS = {"lawbench", "lexeval", "casegen"}
HIGH_PRIORITY_SOURCES = {"legalbench", "lawbench", "legalbench-rag", "lexeval", "cuad"}


class LegalPublicFixturePriorityQueueService:
    """Prioritize public-benchmark-inspired synthetic fixture work without importing datasets."""

    def __init__(
        self,
        sampler_service: LegalPublicBenchmarkSamplerService | None = None,
        crosswalk_service: LegalBenchmarkFixtureCrosswalkService | None = None,
        user_need_service: UserNeedBenchmarkCoverageService | None = None,
        document_coverage_service: LegalDocumentBenchmarkCoverageService | None = None,
        local_baseline_service: LegalDocumentBenchmarkFixturesService | None = None,
        corpus_service: SmallLegalDocumentCorpusExpansionService | None = None,
    ) -> None:
        self.sampler_service = sampler_service or LegalPublicBenchmarkSamplerService()
        self.crosswalk_service = crosswalk_service or LegalBenchmarkFixtureCrosswalkService()
        self.user_need_service = user_need_service or UserNeedBenchmarkCoverageService()
        self.document_coverage_service = document_coverage_service or LegalDocumentBenchmarkCoverageService()
        self.local_baseline_service = local_baseline_service or LegalDocumentBenchmarkFixturesService()
        self.corpus_service = corpus_service or SmallLegalDocumentCorpusExpansionService()

    def build_queue(self) -> dict[str, Any]:
        sampler = self.sampler_service.build_plan()
        crosswalk = self.crosswalk_service.build_crosswalk()
        user_need_coverage = self.user_need_service.build_coverage()
        document_coverage = self.document_coverage_service.build_matrix()
        local_baseline = self.local_baseline_service.build_local_rule_baseline()
        corpus = self.corpus_service.build_corpus()

        batches_by_source = self._batches_by_source(sampler)
        user_needs_by_source = self._user_needs_by_source(user_need_coverage)
        document_gap_shapes = self._document_gap_shapes(document_coverage)
        rows = [
            self._queue_row(
                source_row,
                sampler,
                batches_by_source,
                user_needs_by_source,
                document_gap_shapes,
                local_baseline,
            )
            for source_row in crosswalk["source_rows"]
        ]
        rows = sorted(rows, key=lambda row: (-row["priority_score"], row["source_id"]))
        high_priority_rows = [row for row in rows if row["priority_band"] == "high"]
        license_watch_rows = [
            row for row in rows if "license_review_required" in row["reason_codes"]
        ]
        fixture_gap_rows = [
            row
            for row in rows
            if "document_fixture_mapping_missing" in row["reason_codes"]
            or "small_corpus_mapping_missing" in row["reason_codes"]
        ]
        chinese_rows = [row for row in rows if row["source_id"] in CHINESE_LEGAL_SOURCE_IDS]

        return {
            "status": self._status(rows, local_baseline),
            "method": {
                "type": "public-benchmark-to-synthetic-fixture-priority-queue",
                "purpose": (
                    "Turn public legal benchmark source metadata into the next low-resource synthetic fixture "
                    "work queue without downloading datasets or copying public examples."
                ),
                "source_services": [
                    "legal_public_benchmark_sampler",
                    "legal_benchmark_fixture_crosswalk",
                    "user_need_benchmark_coverage",
                    "legal_document_benchmark_coverage",
                    "legal_document_benchmark_fixtures.local_rule_baseline",
                    "small_legal_document_corpus_expansion",
                ],
                "research_basis_source_ids": [
                    "legalbench",
                    "lawbench",
                    "lexeval",
                    "casegen",
                    "legalbench-rag",
                    "cuad",
                    "lexglue",
                    "pile-of-law",
                ],
            },
            "summary": {
                "source_count": len(rows),
                "queue_row_count": len(rows),
                "high_priority_row_count": len(high_priority_rows),
                "license_review_required_row_count": len(license_watch_rows),
                "fixture_gap_row_count": len(fixture_gap_rows),
                "chinese_source_count": len(chinese_rows),
                "lawbench_source_present": any(row["source_id"] == "lawbench" for row in rows),
                "lexeval_source_present": any(row["source_id"] == "lexeval" for row in rows),
                "local_rule_baseline_status": local_baseline["status"],
                "local_rule_baseline_score": local_baseline["score"],
                "local_rule_baseline_required": True,
                "document_gap_count": document_coverage["summary"]["missing_document_type_count"],
                "small_corpus_item_count": corpus["summary"]["corpus_item_count"],
                "max_samples_per_source": sampler["summary"]["max_samples_per_source"],
                "model_calls": "not_required",
                "network_access": "disabled",
                "external_dataset_downloads": False,
            },
            "queue_rows": rows,
            "high_priority_source_ids": [row["source_id"] for row in high_priority_rows],
            "license_watch_source_ids": [row["source_id"] for row in license_watch_rows],
            "fixture_gap_source_ids": [row["source_id"] for row in fixture_gap_rows],
            "recommended_actions": self._recommended_actions(rows, local_baseline),
            "privacy_boundary": {
                "returns_public_benchmark_text": False,
                "returns_dataset_examples": False,
                "returns_local_fixture_snippets": False,
                "returns_small_corpus_excerpts": False,
                "returns_model_outputs": False,
                "returns_prompts": False,
                "returns_credentials": False,
                "external_dataset_downloads": False,
                "model_calls": False,
                "network_access": False,
            },
            "claim_boundary": {
                "public_benchmark_score_claimed": False,
                "public_dataset_coverage_claimed": False,
                "production_accuracy_claimed": False,
                "real_client_document_coverage_claimed": False,
                "default_model_changed": False,
                "allowed_claim": (
                    "Metadata-only queue for building synthetic fixtures inspired by reviewed public benchmark task taxonomies."
                ),
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_public_fixture_priority_queue.py -q",
                "cd app/backend && python -m pytest tests/test_legal_public_benchmark_sampler.py tests/test_legal_benchmark_fixture_crosswalk.py tests/test_user_need_benchmark_coverage.py -q",
            ],
        }

    def _queue_row(
        self,
        source_row: dict[str, Any],
        sampler: dict[str, Any],
        batches_by_source: dict[str, list[str]],
        user_needs_by_source: dict[str, list[dict[str, Any]]],
        document_gap_shapes: list[dict[str, Any]],
        local_baseline: dict[str, Any],
    ) -> dict[str, Any]:
        source_id = str(source_row["source_id"])
        user_need_rows = user_needs_by_source.get(source_id, [])
        reason_codes = self._reason_codes(source_row, user_need_rows, local_baseline)
        priority_score = self._priority_score(source_row, user_need_rows, reason_codes)
        return {
            "id": f"public-fixture-priority-{source_id}",
            "source_id": source_id,
            "title": source_row["title"],
            "priority_band": self._priority_band(priority_score),
            "priority_score": priority_score,
            "sampling_state": source_row["sampling_state"],
            "resource_profile": source_row["resource_profile"],
            "validation_targets": list(source_row["validation_targets"]),
            "linked_user_need_ids": [row["need_id"] for row in user_need_rows],
            "linked_high_priority_need_ids": [
                row["need_id"] for row in user_need_rows if row["priority_band"] == "high"
            ],
            "benchmark_case_ids": list(source_row["benchmark_case_ids"]),
            "local_fixture_ids": list(source_row["local_fixture_ids"]),
            "document_fixture_ids": list(source_row["document_fixture_ids"]),
            "small_corpus_item_ids": list(source_row["small_corpus_item_ids"]),
            "sampling_batch_ids": batches_by_source.get(source_id, []),
            "recommended_synthetic_fixture_shapes": self._recommended_shapes(
                source_row,
                document_gap_shapes,
            ),
            "gate_status": self._gate_status(reason_codes, local_baseline),
            "reason_codes": reason_codes,
            "next_validation_target": "/api/v1/maintenance/legal-review-benchmark/public-fixture-priority-queue",
            "raw_text_returned": False,
            "model_calls": "not_required",
            "network_access": "disabled",
        }

    def _batches_by_source(self, sampler: dict[str, Any]) -> dict[str, list[str]]:
        batches: dict[str, list[str]] = {}
        for batch in sampler.get("sampling_batches", []):
            batch_id = str(batch["id"])
            for source_id in batch.get("source_ids", []):
                batches.setdefault(str(source_id), []).append(batch_id)
        return {source_id: sorted(set(batch_ids)) for source_id, batch_ids in batches.items()}

    def _user_needs_by_source(self, user_need_coverage: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        rows_by_source: dict[str, list[dict[str, Any]]] = {}
        for row in user_need_coverage.get("coverage_rows", []):
            public_sources = row.get("linked_public_source_ids") or []
            if not isinstance(public_sources, list):
                continue
            slim_row = {
                "need_id": row["need_id"],
                "priority_band": row["priority_band"],
                "coverage_status": row["coverage_status"],
                "public_benchmark_status": row["public_benchmark_status"],
            }
            for source_id in public_sources:
                rows_by_source.setdefault(str(source_id), []).append(slim_row)
        return rows_by_source

    def _document_gap_shapes(self, document_coverage: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "document_type": item["document_type"],
                "recommended_fixture_shape": item["recommended_fixture_shape"],
            }
            for item in document_coverage.get("next_fixture_queue", [])
        ]

    def _reason_codes(
        self,
        source_row: dict[str, Any],
        user_need_rows: list[dict[str, Any]],
        local_baseline: dict[str, Any],
    ) -> list[str]:
        source_id = str(source_row["source_id"])
        codes: list[str] = []
        if local_baseline["status"] != "pass":
            codes.append("local_rule_baseline_not_pass")
        if source_row["sampling_state"] == "license_review_required":
            codes.append("license_review_required")
        if source_row["sampling_state"] == "catalog_only":
            codes.append("catalog_reference_only")
        if not source_row["document_fixture_ids"]:
            codes.append("document_fixture_mapping_missing")
        if not source_row["small_corpus_item_ids"]:
            codes.append("small_corpus_mapping_missing")
        if source_id in CHINESE_LEGAL_SOURCE_IDS:
            codes.append("chinese_legal_source")
        if source_id == "lawbench":
            codes.append("lawbench_task_taxonomy")
        if any(row["priority_band"] == "high" for row in user_need_rows):
            codes.append("high_priority_user_need_linked")
        if not user_need_rows:
            codes.append("user_need_mapping_missing")
        return codes

    def _priority_score(
        self,
        source_row: dict[str, Any],
        user_need_rows: list[dict[str, Any]],
        reason_codes: list[str],
    ) -> int:
        source_id = str(source_row["source_id"])
        score = 40
        if source_id in HIGH_PRIORITY_SOURCES or source_row["priority"] == "high":
            score += 25
        if "chinese_legal_source" in reason_codes:
            score += 15
        if "high_priority_user_need_linked" in reason_codes:
            score += 15
        if "document_fixture_mapping_missing" in reason_codes:
            score += 10
        if "small_corpus_mapping_missing" in reason_codes:
            score += 5
        if source_row["sampling_state"] == "catalog_only":
            score -= 15
        if source_row["sampling_state"] == "license_review_required":
            score += 5
        if not user_need_rows:
            score -= 10
        return max(0, min(100, score))

    def _priority_band(self, score: int) -> str:
        if score >= 75:
            return "high"
        if score >= 50:
            return "medium"
        return "low"

    def _recommended_shapes(
        self,
        source_row: dict[str, Any],
        document_gap_shapes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not source_row["document_fixture_ids"]:
            return document_gap_shapes[:2] or [
                {
                    "document_type": "synthetic_legal_document",
                    "recommended_fixture_shape": "Add a short synthetic legal document with structure, citations, risk labels, and PII exclusions.",
                }
            ]
        shapes = [
            {
                "document_type": row["document_type"],
                "recommended_fixture_shape": (
                    f"Add a source-aligned synthetic variant for {source_row['source_id']} using fixture {row['case_id']} "
                    "without copying public benchmark text."
                ),
            }
            for row in source_row["document_fixture_rows"][:2]
        ]
        if source_row["source_id"] == "lawbench":
            shapes.insert(
                0,
                {
                    "document_type": "zh_cn_legal_reasoning_fixture",
                    "recommended_fixture_shape": (
                        "Add a Chinese synthetic legal reasoning fixture covering classification, evidence reasoning, "
                        "and citation checks from the LawBench task taxonomy."
                    ),
                },
            )
        return shapes[:3]

    def _gate_status(self, reason_codes: list[str], local_baseline: dict[str, Any]) -> str:
        if local_baseline["status"] != "pass":
            return "blocked_until_local_baseline_passes"
        if "document_fixture_mapping_missing" in reason_codes or "small_corpus_mapping_missing" in reason_codes:
            return "needs_synthetic_fixture_mapping"
        if "license_review_required" in reason_codes:
            return "metadata_only_until_license_review"
        if "catalog_reference_only" in reason_codes:
            return "catalog_reference_only"
        return "ready_for_synthetic_fixture_design"

    def _status(self, rows: list[dict[str, Any]], local_baseline: dict[str, Any]) -> str:
        if local_baseline["status"] != "pass":
            return "blocked"
        if any(row["priority_band"] == "high" for row in rows):
            return "ready_with_priority_queue"
        return "ready"

    def _recommended_actions(self, rows: list[dict[str, Any]], local_baseline: dict[str, Any]) -> list[str]:
        if local_baseline["status"] != "pass":
            return [
                "Do not add public-benchmark-inspired samples until the local rule baseline passes.",
                "Fix local legal-document fixture labels and fields before expanding the queue.",
            ]
        top_rows = rows[:3]
        return [
            "Add only synthetic zh-CN fixture variants from this queue; do not copy public benchmark examples into git.",
            "Start with high-priority LawBench/LexEval/LegalBench-RAG rows when expanding legal reasoning and document-generation coverage.",
            "Keep every new fixture tied to a user_need_id, local validation command, and license review state.",
            "Run the local rule baseline and public fixture priority queue tests before promoting cheap-first model evidence.",
            "Top queued sources: " + ", ".join(row["source_id"] for row in top_rows) + ".",
        ]
