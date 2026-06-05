from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


FORBIDDEN_CONTENT_LABELS = (
    "raw_legal_text",
    "prompt",
    "model_output",
    "credentials",
    "gateway_payload",
)


@dataclass(frozen=True)
class AuthorityRule:
    id: str
    title: str
    requirement: str
    severity: str
    evidence_fields: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_fields"] = list(self.evidence_fields)
        return data


@dataclass(frozen=True)
class CitationRule:
    id: str
    title: str
    requirement: str
    blocks_release: bool
    evidence_fields: tuple[str, ...]

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_fields"] = list(self.evidence_fields)
        return data


class LegalRagAuthorityCitationGateService:
    """Build metadata-only authority and citation quality evidence for Legal RAG."""

    def build_gate(self) -> dict[str, Any]:
        authority_rules = self._authority_rules()
        citation_rules = self._citation_rules()
        source_rows = self._source_rows()
        citation_mismatch_rows = [
            row for row in source_rows if row["citation_mismatch_count"] > 0
        ]
        retrieval_gap_rows = [row for row in source_rows if row["retrieval_gap_count"] > 0]
        freshness_gap_rows = [
            row for row in source_rows if row["freshness_status"] in {"review_due", "stale", "blocked"}
        ]
        release_links = (
            "legal-rag-selected-source-request-metadata",
            "legal-rag-selected-source-citation-validation",
            "legal-rag-index-binding",
            "legal-source-freshness-policy",
            "deep-review-selected-source-binding",
            "case-export-readiness",
            "frontend-ui-regression-gate",
        )

        return {
            "status": "ready",
            "id": "legal-rag-authority-citation-gate",
            "title": "Legal RAG authority and citation quality gate",
            "method": {
                "type": "metadata-only-authority-citation-gate",
                "notes": [
                    "Evaluates source authority and citation quality using metadata labels, source ids, timestamps, jurisdiction tags, and validation flags only.",
                    "Does not call NewAPI, Gemini, model gateways, crawlers, or external benchmark datasets.",
                    "Does not save raw legal text, prompts, model output, gateway payloads, credentials, account data, or client material.",
                    "Designed as release/readiness, continuous ledger, OSS maintenance, and frontend regression protected-panel evidence.",
                ],
            },
            "summary": {
                "authority_rule_count": len(authority_rules),
                "citation_rule_count": len(citation_rules),
                "release_gate_link_count": len(release_links),
                "metadata_only": True,
                "network_access": "disabled",
                "model_calls": "disabled",
                "raw_content_storage": "forbidden",
                "blocks_broad_claims_without_reviewer_evidence": True,
                "source_tier_count": len({row["source_tier"] for row in source_rows}),
                "authority_review_count": len(source_rows),
                "jurisdiction_count": len({row["jurisdiction"] for row in source_rows}),
                "freshness_gap_count": len(freshness_gap_rows),
                "stale_source_count": sum(1 for row in source_rows if row["freshness_status"] == "stale"),
                "citation_mismatch_count": len(citation_mismatch_rows),
                "retrieval_gap_count": len(retrieval_gap_rows),
            },
            "authority_rules": [rule.to_api() for rule in authority_rules],
            "citation_rules": [rule.to_api() for rule in citation_rules],
            "source_tiers": {
                "primary_official": "Statutes, regulations, judicial interpretations, court materials, or official guidance metadata.",
                "approved_secondary": "Repository-approved templates, practice references, or explainers with reviewer labels.",
                "unknown_or_stale": "Unknown, stale, unmatched, or secondary-only metadata that must stay review-required.",
            },
            "jurisdiction_counts": self._counter(source_rows, "jurisdiction"),
            "source_rows": source_rows,
            "citation_mismatch_rows": citation_mismatch_rows,
            "retrieval_gap_rows": retrieval_gap_rows,
            "required_metadata_fields": [
                "source_id",
                "source_type",
                "authority_tier",
                "jurisdiction",
                "publication_or_effective_date",
                "retrieval_plan_id",
                "selected_source_ids",
                "citation_map_source_ids",
                "freshness_status",
                "validation_status",
            ],
            "release_gate_links": list(release_links),
            "evidence_paths": [
                "app/backend/services/legal_rag_authority_citation_gate.py",
                "app/backend/tests/test_legal_rag_authority_citation_gate.py",
                "app/backend/services/legal_rag_selected_source_validation.py",
                "app/backend/services/legal_rag_request_metadata.py",
                "app/backend/services/legal_rag_index_binding.py",
                "docs/LEGAL_RAG_AUTHORITY_CITATION_GATE.md",
            ],
            "recommended_actions": [
                "Keep primary legal authorities, official sources, and selected-source ids distinguishable from secondary or unknown source metadata.",
                "Block delivery when citation_map source ids do not match selected-source metadata or when authority tier, jurisdiction, or freshness fields are missing.",
                "Surface the gate on release, maintenance, ledger, and frontend regression evidence without rendering legal snippets or model text.",
            ],
            "claim_boundary": {
                "legal_advice_claimed": False,
                "unsupported_claims_allowed": False,
                "citation_without_source_allowed": False,
                "jurisdiction_mismatch_allowed": False,
                "freshness_gap_allowed": False,
                "public_benchmark_score_claimed": False,
                "live_rag_accuracy_claimed": False,
            },
            "privacy_boundary": {
                "metadata_only": True,
                "calls_newapi": False,
                "calls_gemini": False,
                "calls_gateway": False,
                "downloads_datasets": False,
                "stores_raw_legal_text": False,
                "stores_prompt": False,
                "stores_model_output": False,
                "stores_credentials": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_raw_model_output": False,
                "returns_credentials": False,
                "returns_gateway_payloads": False,
                "forbidden_content_labels": list(FORBIDDEN_CONTENT_LABELS),
            },
            "validation_commands": [
                "python -m pytest tests/test_legal_rag_authority_citation_gate.py -q",
                "python -m pytest tests/test_legal_rag_authority_citation_gate.py tests/test_release_readiness.py tests/test_continuous_update_ledger.py tests/test_maintenance_evidence.py tests/test_frontend_ui_regression_gate.py -q",
            ],
        }

    def _source_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "cn-contract-code-authority",
                "source_id": "cn-contract-code",
                "title": "Civil Code contract chapter metadata",
                "source_tier": "primary_official",
                "authority_level": "national_statute",
                "source_type": "statute",
                "jurisdiction": "CN-National",
                "freshness_status": "fresh",
                "citation_mismatch_count": 0,
                "retrieval_gap_count": 0,
                "status": "ready",
            },
            {
                "id": "bj-labor-rule-authority",
                "source_id": "bj-labor-rule",
                "title": "Beijing labor rule metadata",
                "source_tier": "primary_official",
                "authority_level": "local_regulation",
                "source_type": "regulation",
                "jurisdiction": "CN-Beijing",
                "freshness_status": "review_due",
                "citation_mismatch_count": 0,
                "retrieval_gap_count": 0,
                "status": "review_required",
            },
            {
                "id": "selected-source-mismatch-watch",
                "source_id": "external-source",
                "title": "Unselected cited source metadata",
                "source_tier": "unknown_or_stale",
                "authority_level": "unknown",
                "source_type": "unknown",
                "jurisdiction": "unknown",
                "freshness_status": "unknown",
                "citation_mismatch_count": 1,
                "retrieval_gap_count": 0,
                "status": "blocked",
            },
            {
                "id": "stale-shanghai-rule-gap",
                "source_id": "stale-shanghai-rule",
                "title": "Stale Shanghai regulation metadata",
                "source_tier": "unknown_or_stale",
                "authority_level": "local_regulation",
                "source_type": "regulation",
                "jurisdiction": "CN-Shanghai",
                "freshness_status": "stale",
                "citation_mismatch_count": 0,
                "retrieval_gap_count": 1,
                "status": "blocked",
            },
        ]

    def _counter(self, rows: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            value = str(row.get(field) or "unknown")
            counts[value] = counts.get(value, 0) + 1
        return dict(sorted(counts.items()))

    def _authority_rules(self) -> tuple[AuthorityRule, ...]:
        return (
            AuthorityRule(
                id="primary-official-source-preferred",
                title="Primary and official source preference",
                requirement="Prefer statutes, regulations, court materials, official guidance, or repository-approved source metadata before secondary commentary.",
                severity="blocker",
                evidence_fields=("source_type", "authority_tier", "source_id"),
            ),
            AuthorityRule(
                id="jurisdiction-and-date-required",
                title="Jurisdiction and date required",
                requirement="Require jurisdiction and publication or effective date metadata before treating a source as authoritative.",
                severity="blocker",
                evidence_fields=("jurisdiction", "publication_or_effective_date", "freshness_status"),
            ),
            AuthorityRule(
                id="unknown-authority-needs-review",
                title="Unknown authority needs review",
                requirement="Route unknown, stale, secondary-only, or unsupported authority metadata to lawyer or maintainer review.",
                severity="review",
                evidence_fields=("authority_tier", "validation_status", "review_required"),
            ),
        )

    def _citation_rules(self) -> tuple[CitationRule, ...]:
        return (
            CitationRule(
                id="citation-source-id-match",
                title="Citation source ids match selected sources",
                requirement="Every citation_map source id must be present in selected_source_ids or the retrieval plan metadata.",
                blocks_release=True,
                evidence_fields=("selected_source_ids", "citation_map_source_ids", "retrieval_plan_id"),
            ),
            CitationRule(
                id="no-unsupported-citation-claims",
                title="Unsupported citation claims blocked",
                requirement="Do not mark a report deliverable when citations are missing, stale, unmatched, or authority metadata is incomplete.",
                blocks_release=True,
                evidence_fields=("validation_status", "freshness_status", "blocking_check_ids"),
            ),
            CitationRule(
                id="metadata-only-citation-review",
                title="Metadata-only citation review",
                requirement="Expose citation quality as source ids, counts, statuses, and evidence paths only, never as snippets or generated analysis.",
                blocks_release=True,
                evidence_fields=("source_id", "status", "evidence_paths"),
            ),
        )
