from __future__ import annotations

from typing import Any

from services.feedback_issue_cluster import FeedbackIssueClusterService
from services.feedback_roadmap_alignment import FeedbackRoadmapAlignmentService
from services.legal_document_benchmark_coverage import LegalDocumentBenchmarkCoverageService
from services.user_need_benchmark_coverage import UserNeedBenchmarkCoverageService
from services.user_need_legal_document_benchmark_evidence import (
    UserNeedLegalDocumentBenchmarkEvidenceService,
)
from services.user_needs_radar import UserNeedsRadarService


SEVERITY_WEIGHT = {"critical": 40, "high": 30, "medium": 18, "low": 8}
PRIORITY_BAND_WEIGHT = {"high": 18, "medium": 9, "low": 3}

TOPIC_NEED_HINTS: dict[str, tuple[str, ...]] = {
    "privacy_or_security_exposure": ("privacy-safe-upload", "prompt-injection-resilience"),
    "legal_output_quality_risk": ("traceable-legal-review",),
    "document_upload_or_extraction_failure": ("robust-extraction-quality",),
    "export_or_delivery_format_issue": ("plain-language-actionability",),
    "performance_or_reliability_issue": ("cheap-first-review-routing",),
    "feature_or_usability_request": ("plain-language-actionability", "feedback-to-roadmap-loop"),
    "payment_or_access_blocker": ("feedback-to-roadmap-loop",),
    "general_feedback": ("feedback-to-roadmap-loop",),
}

TOPIC_DOCUMENT_TYPE_HINTS: dict[str, tuple[str, ...]] = {
    "legal_output_quality_risk": ("legal_opinion", "civil_complaint", "defense_answer"),
    "document_upload_or_extraction_failure": ("evidence_catalog",),
    "export_or_delivery_format_issue": ("settlement_agreement", "lawyer_letter"),
    "feature_or_usability_request": ("lawyer_letter", "legal_opinion"),
    "privacy_or_security_exposure": ("civil_complaint", "evidence_catalog"),
    "performance_or_reliability_issue": ("contract_review",),
    "payment_or_access_blocker": ("lawyer_letter",),
    "general_feedback": ("lawyer_letter",),
}


class FeedbackUserNeedLegalDocumentBenchmarkBacklogService:
    """Map privacy-safe feedback clusters into user-need benchmark backlog rows."""

    def __init__(
        self,
        cluster_service: FeedbackIssueClusterService | None = None,
        alignment_service: FeedbackRoadmapAlignmentService | None = None,
        user_needs_service: UserNeedsRadarService | None = None,
        coverage_service: UserNeedBenchmarkCoverageService | None = None,
        document_coverage_service: LegalDocumentBenchmarkCoverageService | None = None,
        document_evidence_service: UserNeedLegalDocumentBenchmarkEvidenceService | None = None,
    ) -> None:
        self.cluster_service = cluster_service or FeedbackIssueClusterService()
        self.alignment_service = alignment_service or FeedbackRoadmapAlignmentService()
        self.user_needs_service = user_needs_service or UserNeedsRadarService()
        self.coverage_service = coverage_service or UserNeedBenchmarkCoverageService()
        self.document_coverage_service = document_coverage_service or LegalDocumentBenchmarkCoverageService()
        self.document_evidence_service = document_evidence_service or UserNeedLegalDocumentBenchmarkEvidenceService()

    def build_backlog(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        items = self._feedback_items(payload)
        cluster_report = self.cluster_service.cluster(items)
        radar = self.user_needs_service.build_radar()
        coverage = self.coverage_service.build_coverage()
        document_coverage = self.document_coverage_service.build_matrix()
        document_evidence = self.document_evidence_service.build_bridge(
            self._safe_mapping(payload.get("legal_document_evidence"))
        )

        needs_by_id = {str(need["id"]): need for need in radar.get("needs", []) if isinstance(need, dict)}
        coverage_by_need_id = {
            str(row["need_id"]): row
            for row in coverage.get("coverage_rows", [])
            if isinstance(row, dict) and row.get("need_id")
        }
        evidence_by_need_id = {
            str(row["need_id"]): row
            for row in document_evidence.get("evidence_rows", [])
            if isinstance(row, dict) and row.get("need_id")
        }
        document_type_rows = {
            str(row["label"]): row
            for row in document_coverage.get("dimensions", {}).get("document_types", [])
            if isinstance(row, dict) and row.get("label")
        }

        backlog_rows = [
            self._backlog_row(
                cluster=cluster,
                needs_by_id=needs_by_id,
                coverage_by_need_id=coverage_by_need_id,
                evidence_by_need_id=evidence_by_need_id,
                document_type_rows=document_type_rows,
            )
            for cluster in cluster_report.get("clusters", [])
            if isinstance(cluster, dict)
        ]
        backlog_rows.sort(
            key=lambda row: (
                -int(row["priority_score"]),
                row["benchmark_action_status"],
                row["cluster_id"],
            )
        )

        blocked_rows = [row for row in backlog_rows if row["benchmark_action_status"] == "blocked"]
        fixture_rows = [row for row in backlog_rows if row["benchmark_action_status"] == "create_fixture"]
        review_rows = [row for row in backlog_rows if row["benchmark_action_status"] == "review_required"]
        ready_rows = [row for row in backlog_rows if row["benchmark_action_status"] == "ready"]
        status = "blocked" if blocked_rows else ("ready_with_backlog" if fixture_rows or review_rows else "ready")

        return {
            "status": status,
            "method": {
                    "type": "feedback-user-need-legal-document-benchmark-backlog",
                "notes": [
                    "Clusters feedback with deterministic local rules, maps clusters to user_need IDs, then joins user-need benchmark coverage and legal-document evidence.",
                    "Ranks benchmark backlog rows by severity, feedback count, user-need priority, and legal-document evidence status.",
                    "Returns normalized topics, counts, safe refs, IDs, statuses, and actions only; raw feedback, PII, prompts, model outputs, payload bodies, and credentials are not returned.",
                ],
            },
            "summary": {
                "input_item_count": cluster_report["summary"]["input_item_count"],
                "processed_item_count": cluster_report["summary"]["processed_item_count"],
                "cluster_count": len(backlog_rows),
                "ready_row_count": len(ready_rows),
                "create_fixture_row_count": len(fixture_rows),
                "review_required_row_count": len(review_rows),
                "blocked_row_count": len(blocked_rows),
                "high_or_critical_feedback_cluster_count": sum(
                    1 for row in backlog_rows if row["severity"] in {"critical", "high"}
                ),
                "mapped_need_count": len({need_id for row in backlog_rows for need_id in row["mapped_need_ids"]}),
                "document_type_suggestion_count": sum(
                    len(row["suggested_document_type_ids"]) for row in backlog_rows
                ),
                "raw_feedback_returned": False,
                "model_calls": "not_required",
                "network_access": "disabled",
            },
            "backlog_rows": backlog_rows,
            "blocked_cluster_ids": [row["cluster_id"] for row in blocked_rows],
            "create_fixture_cluster_ids": [row["cluster_id"] for row in fixture_rows],
            "review_required_cluster_ids": [row["cluster_id"] for row in review_rows],
            "source_summaries": {
                "feedback_clusters": cluster_report["summary"],
                "user_need_benchmark_coverage": coverage["summary"],
                "legal_document_evidence": document_evidence["summary"],
                "legal_document_coverage": document_coverage["summary"],
            },
            "recommended_actions": self._recommended_actions(blocked_rows, fixture_rows, review_rows, ready_rows),
            "privacy_boundary": {
                "metadata_only": True,
                "returns_raw_feedback": False,
                "returns_raw_feedback_text": False,
                "returns_feedback_body": False,
                "returns_user_feedback_text": False,
                "returns_pii": False,
                "returns_document_snippets": False,
                "returns_fixture_snippets": False,
                "returns_public_benchmark_text": False,
                "returns_prompt_text": False,
                "returns_raw_model_output": False,
                "returns_payload_bodies": False,
                "returns_credentials": False,
                "model_calls": False,
                "network_called": False,
            },
            "claim_boundary": {
                "production_quality_claimed": False,
                "feedback_resolution_claimed": False,
                "public_benchmark_score_claimed": False,
                "client_document_coverage_claimed": False,
                "allowed_claim": (
                    "The repository maps privacy-safe feedback clusters to user-need and legal-document "
                    "benchmark backlog metadata for maintainer review."
                ),
            },
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_feedback_user_need_legal_document_benchmark_backlog.py -q",
                "cd app/backend && python -m pytest tests/test_feedback_issue_cluster.py tests/test_feedback_roadmap_alignment.py tests/test_user_need_legal_document_benchmark_evidence.py tests/test_user_need_implementation_priority_queue.py -q",
            ],
        }

    def _backlog_row(
        self,
        *,
        cluster: dict[str, Any],
        needs_by_id: dict[str, dict[str, Any]],
        coverage_by_need_id: dict[str, dict[str, Any]],
        evidence_by_need_id: dict[str, dict[str, Any]],
        document_type_rows: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        topic = str(cluster.get("normalized_topic") or "general_feedback")
        mapped_need_ids = self._mapped_need_ids(topic, needs_by_id)
        primary_need_id = mapped_need_ids[0] if mapped_need_ids else "feedback-to-roadmap-loop"
        primary_need = needs_by_id.get(primary_need_id, {})
        primary_coverage = coverage_by_need_id.get(primary_need_id, {})
        primary_evidence = evidence_by_need_id.get(primary_need_id, {})
        suggested_document_type_ids = self._suggested_document_type_ids(topic, document_type_rows, primary_evidence)
        evidence_status = str(primary_evidence.get("evidence_status") or "not_run")
        action_status = self._action_status(cluster, primary_need, primary_evidence, suggested_document_type_ids)
        priority_score = self._priority_score(cluster, primary_need, primary_evidence, suggested_document_type_ids)
        reason_codes = self._reason_codes(
            topic,
            cluster,
            primary_need,
            primary_coverage,
            primary_evidence,
            suggested_document_type_ids,
            action_status,
        )

        return {
            "cluster_id": str(cluster.get("cluster_id") or f"feedback-{topic}"),
            "normalized_topic": topic,
            "severity": str(cluster.get("severity") or "low"),
            "feedback_count": int(cluster.get("count") or 0),
            "safe_evidence_ref_count": len(cluster.get("evidence_refs") or []),
            "affected_user_segment_tags": list(cluster.get("affected_user_segment_tags") or []),
            "mapped_need_ids": mapped_need_ids,
            "primary_need_id": primary_need_id,
            "primary_need_title": primary_need.get("title") or primary_need_id,
            "primary_need_priority_band": primary_need.get("priority_band") or "low",
            "primary_need_category": primary_need.get("category") or "maintenance",
            "benchmark_action_status": action_status,
            "priority_score": priority_score,
            "coverage_status": primary_coverage.get("coverage_status") or "gap",
            "legal_document_evidence_status": evidence_status,
            "linked_benchmark_case_ids": list(primary_coverage.get("linked_benchmark_case_ids") or []),
            "linked_document_case_ids": list(primary_evidence.get("document_case_ids") or []),
            "linked_document_type_ids": list(primary_evidence.get("document_type_ids") or []),
            "suggested_document_type_ids": suggested_document_type_ids,
            "suggested_fixture_ids": [f"feedback-{topic}-{document_type}" for document_type in suggested_document_type_ids],
            "release_gate_links": sorted(
                set(primary_need.get("release_gate_links") or [])
                | set(primary_coverage.get("linked_release_gates") or [])
                | {"feedback-user-need-legal-document-benchmark-backlog"}
            ),
            "reason_codes": reason_codes,
            "next_actions": self._next_actions(topic, action_status, primary_need_id, suggested_document_type_ids),
        }

    def _mapped_need_ids(self, topic: str, needs_by_id: dict[str, dict[str, Any]]) -> list[str]:
        mapped = [need_id for need_id in TOPIC_NEED_HINTS.get(topic, ()) if need_id in needs_by_id]
        if mapped:
            return mapped
        alignment = self.alignment_service.align({"category": topic, "content": topic.replace("_", " ")})
        aligned = [str(match["need_id"]) for match in alignment.get("matches", []) if match.get("need_id") in needs_by_id]
        return aligned or (["feedback-to-roadmap-loop"] if "feedback-to-roadmap-loop" in needs_by_id else [])

    def _suggested_document_type_ids(
        self,
        topic: str,
        document_type_rows: dict[str, dict[str, Any]],
        primary_evidence: dict[str, Any],
    ) -> list[str]:
        existing = set(primary_evidence.get("document_type_ids") or [])
        suggestions: list[str] = []
        for document_type in TOPIC_DOCUMENT_TYPE_HINTS.get(topic, ("lawyer_letter",)):
            row = document_type_rows.get(document_type, {})
            if document_type not in existing or not row.get("covered"):
                suggestions.append(document_type)
        return _unique(suggestions)[:3]

    def _action_status(
        self,
        cluster: dict[str, Any],
        need: dict[str, Any],
        evidence: dict[str, Any],
        suggested_document_type_ids: list[str],
    ) -> str:
        severity = str(cluster.get("severity") or "low")
        evidence_status = str(evidence.get("evidence_status") or "not_run")
        priority_band = str(need.get("priority_band") or "low")
        if severity in {"critical", "high"} and evidence_status == "blocked":
            return "blocked"
        if suggested_document_type_ids:
            return "create_fixture"
        if evidence_status in {"not_run", "review_required"} or priority_band == "high":
            return "review_required"
        return "ready"

    def _priority_score(
        self,
        cluster: dict[str, Any],
        need: dict[str, Any],
        evidence: dict[str, Any],
        suggested_document_type_ids: list[str],
    ) -> int:
        severity = str(cluster.get("severity") or "low")
        count = int(cluster.get("count") or 0)
        priority_band = str(need.get("priority_band") or "low")
        evidence_status = str(evidence.get("evidence_status") or "not_run")
        score = SEVERITY_WEIGHT.get(severity, 8)
        score += min(20, count * 4)
        score += PRIORITY_BAND_WEIGHT.get(priority_band, 3)
        if evidence_status == "blocked":
            score += 15
        elif evidence_status in {"not_run", "review_required"}:
            score += 8
        score += min(9, len(suggested_document_type_ids) * 3)
        return min(100, score)

    def _reason_codes(
        self,
        topic: str,
        cluster: dict[str, Any],
        need: dict[str, Any],
        coverage: dict[str, Any],
        evidence: dict[str, Any],
        suggested_document_type_ids: list[str],
        action_status: str,
    ) -> list[str]:
        codes = [f"feedback-topic-{topic}", f"action-{action_status}"]
        severity = str(cluster.get("severity") or "low")
        if severity in {"critical", "high"}:
            codes.append("high-risk-feedback")
        if coverage.get("coverage_status") in {"gap", "partial"}:
            codes.append(f"user-need-coverage-{coverage.get('coverage_status')}")
        evidence_status = str(evidence.get("evidence_status") or "not_run")
        if evidence_status != "ready":
            codes.append(f"legal-document-evidence-{evidence_status}")
        if suggested_document_type_ids:
            codes.append("document-fixture-suggestions-present")
        if need.get("priority_band") == "high":
            codes.append("high-priority-user-need")
        return _unique(codes)

    def _next_actions(
        self,
        topic: str,
        action_status: str,
        primary_need_id: str,
        suggested_document_type_ids: list[str],
    ) -> list[str]:
        actions = [f"Keep feedback cluster {topic} linked to user need {primary_need_id}."]
        if action_status == "blocked":
            actions.append("Do not claim this feedback theme is covered until linked document evidence blockers clear.")
        if suggested_document_type_ids:
            actions.append(
                "Create or extend synthetic legal-document fixtures for: "
                + ", ".join(suggested_document_type_ids)
                + "."
            )
        if action_status == "review_required":
            actions.append("Review legal-document benchmark evidence before scheduling customer-visible resolution.")
        if action_status == "ready":
            actions.append("Keep this cluster in the release evidence index and monitor recurring count changes.")
        return actions

    def _recommended_actions(
        self,
        blocked_rows: list[dict[str, Any]],
        fixture_rows: list[dict[str, Any]],
        review_rows: list[dict[str, Any]],
        ready_rows: list[dict[str, Any]],
    ) -> list[str]:
        actions: list[str] = []
        if blocked_rows:
            actions.append(
                "Clear blocked feedback benchmark rows before claiming high-risk feedback themes are covered: "
                + ", ".join(row["cluster_id"] for row in blocked_rows[:5])
            )
        if fixture_rows:
            actions.append(
                "Prioritize synthetic legal-document fixture work for feedback clusters: "
                + ", ".join(row["cluster_id"] for row in fixture_rows[:5])
            )
        if review_rows:
            actions.append(
                "Review not-run or partial legal-document evidence before resolving feedback clusters: "
                + ", ".join(row["cluster_id"] for row in review_rows[:5])
            )
        if not actions and ready_rows:
            actions.append("All feedback benchmark backlog rows are ready for maintenance review.")
        return actions or ["Submit privacy-safe feedback items to generate benchmark backlog rows."]

    def _feedback_items(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        items = payload.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        feedback = payload.get("feedback")
        if isinstance(feedback, list):
            return [item for item in feedback if isinstance(item, dict)]
        return list(self._default_items())

    def _default_items(self) -> tuple[dict[str, Any], ...]:
        return (
            {
                "id": "sample-legal-quality-1",
                "category": "report",
                "content": "Incorrect citation and hallucinated legal conclusion in generated report.",
                "segment": "lawyer",
                "severity": "high",
            },
            {
                "id": "sample-upload-1",
                "category": "document",
                "content": "Scanned PDF upload produced blank OCR extraction for a paid user.",
                "segment": "lawyer paid",
                "severity": "medium",
            },
            {
                "id": "sample-usability-1",
                "category": "suggestion",
                "content": "Need clearer next steps and export format for client delivery.",
                "segment": "legal_ops",
                "severity": "low",
            },
        )

    def _safe_mapping(self, value: Any) -> dict[str, Any]:
        return value if isinstance(value, dict) else {}


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
