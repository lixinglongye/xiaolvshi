from __future__ import annotations

from collections import Counter
from typing import Any

from services.legal_document_benchmark_suite import LegalDocumentBenchmarkSuiteService


TARGET_DOCUMENT_TYPES = (
    "civil_complaint",
    "lawyer_letter",
    "contract_review",
    "evidence_catalog",
    "settlement_agreement",
    "legal_opinion",
)

MAX_LOCAL_FIXTURES_PER_RUN = 3


class LegalDocumentBenchmarkCoverageService:
    """Build a metadata-only coverage matrix for tiny legal-document fixtures."""

    def build_matrix(self) -> dict[str, Any]:
        suite = LegalDocumentBenchmarkSuiteService().build_suite()
        cases = suite["benchmark_cases"]
        case_rows = [self._case_row(case) for case in cases]
        document_type_counts = Counter(row["document_type"] for row in case_rows)
        missing_document_types = [
            document_type
            for document_type in TARGET_DOCUMENT_TYPES
            if document_type_counts.get(document_type, 0) == 0
        ]
        dimensions = self._dimensions(case_rows)
        next_fixture_queue = self._next_fixture_queue(missing_document_types, case_rows)
        status = "ready_with_gaps" if missing_document_types else "ready"

        return {
            "status": status,
            "summary": {
                "case_count": len(case_rows),
                "target_document_type_count": len(TARGET_DOCUMENT_TYPES),
                "covered_document_type_count": len(document_type_counts),
                "missing_document_type_count": len(missing_document_types),
                "section_label_count": len(dimensions["required_sections"]),
                "citation_label_count": len(dimensions["expected_citations"]),
                "risk_label_count": len(dimensions["expected_risk_labels"]),
                "pii_category_count": len(dimensions["banned_pii_categories"]),
                "max_local_fixtures_per_run": MAX_LOCAL_FIXTURES_PER_RUN,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "target_document_types": list(TARGET_DOCUMENT_TYPES),
            "missing_document_types": missing_document_types,
            "case_rows": case_rows,
            "dimensions": dimensions,
            "next_fixture_queue": next_fixture_queue,
            "recommended_actions": self._recommended_actions(missing_document_types, next_fixture_queue),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_coverage.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_suite.py -q",
            ],
            "privacy_boundary": {
                "source": "synthetic_inline_fixture_metadata",
                "returns_snippets": False,
                "returns_generated_text": False,
                "returns_raw_model_output": False,
                "returns_client_identifiers": False,
                "external_dataset_downloads": False,
                "model_calls": False,
            },
            "privacy_note": (
                "This matrix reports fixture IDs, document-type coverage, label counts, and missing local "
                "test categories only. It intentionally omits raw fixture snippets, client documents, "
                "raw client documents, prompts, gateway responses, credentials, emails, phone numbers, "
                "and identity numbers."
            ),
        }

    def _case_row(self, case: dict[str, Any]) -> dict[str, Any]:
        required_sections = list(case.get("required_sections") or [])
        expected_citations = list(case.get("expected_citations") or [])
        expected_risk_labels = list(case.get("expected_risk_labels") or [])
        banned_pii_categories = list(case.get("banned_pii_categories") or [])
        return {
            "case_id": case["id"],
            "title": case["title"],
            "document_type": case["document_type"],
            "matter_type": case["matter_type"],
            "required_section_count": len(required_sections),
            "expected_citation_count": len(expected_citations),
            "expected_risk_label_count": len(expected_risk_labels),
            "banned_pii_category_count": len(banned_pii_categories),
            "coverage_axes": {
                "structure": required_sections,
                "citations": expected_citations,
                "risk_labels": expected_risk_labels,
                "pii": banned_pii_categories,
            },
            "local_run_fit": "laptop_safe",
        }

    def _dimensions(self, case_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        return {
            "document_types": self._dimension_rows(
                [
                    {
                        "label": document_type,
                        "case_id": row["case_id"],
                        "document_type": row["document_type"],
                    }
                    for row in case_rows
                    for document_type in [row["document_type"]]
                ],
                include_missing_targets=True,
            ),
            "required_sections": self._dimension_rows(
                [
                    {
                        "label": label,
                        "case_id": row["case_id"],
                        "document_type": row["document_type"],
                    }
                    for row in case_rows
                    for label in row["coverage_axes"]["structure"]
                ]
            ),
            "expected_citations": self._dimension_rows(
                [
                    {
                        "label": label,
                        "case_id": row["case_id"],
                        "document_type": row["document_type"],
                    }
                    for row in case_rows
                    for label in row["coverage_axes"]["citations"]
                ]
            ),
            "expected_risk_labels": self._dimension_rows(
                [
                    {
                        "label": label,
                        "case_id": row["case_id"],
                        "document_type": row["document_type"],
                    }
                    for row in case_rows
                    for label in row["coverage_axes"]["risk_labels"]
                ]
            ),
            "banned_pii_categories": self._dimension_rows(
                [
                    {
                        "label": label,
                        "case_id": row["case_id"],
                        "document_type": row["document_type"],
                    }
                    for row in case_rows
                    for label in row["coverage_axes"]["pii"]
                ]
            ),
        }

    def _dimension_rows(
        self,
        records: list[dict[str, str]],
        *,
        include_missing_targets: bool = False,
    ) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for record in records:
            label = record["label"]
            grouped.setdefault(
                label,
                {
                    "label": label,
                    "case_ids": [],
                    "document_types": set(),
                    "coverage_count": 0,
                },
            )
            grouped[label]["case_ids"].append(record["case_id"])
            grouped[label]["document_types"].add(record["document_type"])
            grouped[label]["coverage_count"] += 1

        if include_missing_targets:
            for target in TARGET_DOCUMENT_TYPES:
                grouped.setdefault(
                    target,
                    {
                        "label": target,
                        "case_ids": [],
                        "document_types": set(),
                        "coverage_count": 0,
                    },
                )

        return [
            {
                "label": row["label"],
                "coverage_count": row["coverage_count"],
                "case_ids": sorted(row["case_ids"]),
                "document_types": sorted(row["document_types"]),
                "covered": row["coverage_count"] > 0,
            }
            for row in sorted(grouped.values(), key=lambda item: (-item["coverage_count"], item["label"]))
        ]

    def _next_fixture_queue(
        self,
        missing_document_types: list[str],
        case_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        queue: list[dict[str, Any]] = []
        for index, document_type in enumerate(missing_document_types, start=1):
            queue.append(
                {
                    "id": f"next-{document_type}",
                    "priority": "high" if index <= 2 else "medium",
                    "document_type": document_type,
                    "reason": "No synthetic local fixture currently covers this document type.",
                    "recommended_fixture_shape": self._fixture_shape(document_type),
                    "validation_target": "/api/v1/maintenance/legal-review-benchmark/document-coverage",
                }
            )

        sparse_rows = [
            row
            for row in case_rows
            if row["expected_citation_count"] < 2
            or row["expected_risk_label_count"] < 3
            or row["required_section_count"] < 5
        ]
        for row in sparse_rows:
            queue.append(
                {
                    "id": f"strengthen-{row['case_id']}",
                    "priority": "medium",
                    "document_type": row["document_type"],
                    "reason": "Existing fixture has a thin coverage axis and should be strengthened before release claims.",
                    "recommended_fixture_shape": "Add one citation, one risk label, and one required section while keeping the snippet synthetic and under 420 characters.",
                    "validation_target": "/api/v1/maintenance/legal-review-benchmark/document-fixtures",
                }
            )

        return queue[:MAX_LOCAL_FIXTURES_PER_RUN]

    def _fixture_shape(self, document_type: str) -> str:
        shapes = {
            "evidence_catalog": "A short evidence-catalog row set with exhibit refs, proof purpose, authenticity status, and missing-source risk.",
            "settlement_agreement": "A short settlement draft with payment schedule, release scope, breach consequence, and execution review labels.",
            "legal_opinion": "A short legal opinion memo with issue, rule, application, conclusion, citation, and confidence sections.",
        }
        return shapes.get(
            document_type,
            "A short synthetic legal document with structure, citation, risk-label, and PII-exclusion expectations.",
        )

    def _recommended_actions(
        self,
        missing_document_types: list[str],
        next_fixture_queue: list[dict[str, Any]],
    ) -> list[str]:
        if not missing_document_types:
            return [
                "Keep the local fixture matrix attached to every legal document benchmark change.",
                "Run the document benchmark suite before claiming coverage improvements.",
            ]

        return [
            "Add synthetic fixtures for missing document types before claiming broad legal-document coverage.",
            f"Prioritize {', '.join(missing_document_types[:3])} in the next low-resource run queue.",
            f"Keep fixture additions capped at {MAX_LOCAL_FIXTURES_PER_RUN} per laptop-safe run.",
            "Review the matrix after each fixture addition and keep raw client documents out of git.",
        ][: 2 + min(2, len(next_fixture_queue))]
