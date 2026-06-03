from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import re
from typing import Any


REFERENCE_DATE = date(2026, 6, 4)
SUPPORTED_JURISDICTIONS = {
    "CN",
    "CN-National",
    "CN-Beijing",
    "CN-Shanghai",
    "CN-Guangdong",
    "CN-Zhejiang",
    "CN-Jiangsu",
}
FRESHNESS_WINDOWS_DAYS = {
    "statute": 365,
    "regulation": 365,
    "judicial_interpretation": 365,
    "case": 730,
    "template": 365,
    "internal_note": 180,
}
SENSITIVE_PATTERN = re.compile(
    r"(s" r"k-[A-Za-z0-9]{20,}|APP_AI_KEY=s" r"k-|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LegalSourceMetadata:
    id: str
    title: str
    source_type: str
    jurisdiction: str
    effective_date: str
    last_verified_at: str
    citation: str
    use_case: str

    def to_api(self) -> dict[str, str]:
        return asdict(self)


class LegalSourceFreshnessPolicyService:
    """Evaluate legal source freshness without storing real case material."""

    def build_policy(
        self,
        sources: list[dict[str, Any]] | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> dict[str, Any]:
        source_items = self._source_items(sources)
        reviews = [self._review_source(item, reference_date) for item in source_items]
        failing = [item for item in reviews if item["status"] == "fail"]
        warnings = [item for item in reviews if item["status"] == "warn"]
        missing_jurisdiction = [item["id"] for item in reviews if "missing_jurisdiction" in item["flags"]]
        stale_sources = [item["id"] for item in reviews if "stale_source" in item["flags"]]

        if failing:
            status = "blocked"
        elif warnings:
            status = "review_recommended"
        else:
            status = "ready"

        return {
            "status": status,
            "summary": {
                "source_count": len(reviews),
                "ready_count": sum(1 for item in reviews if item["status"] == "pass"),
                "warning_count": len(warnings),
                "blocked_count": len(failing),
                "stale_source_ids": stale_sources,
                "missing_jurisdiction_ids": missing_jurisdiction,
                "supported_jurisdictions": sorted(SUPPORTED_JURISDICTIONS),
                "reference_date": reference_date.isoformat(),
            },
            "freshness_rules": self._freshness_rules(),
            "source_reviews": reviews,
            "manual_review_escalations": self._manual_review_escalations(),
            "recommended_actions": self._recommended_actions(failing, warnings),
            "privacy_note": (
                "This privacy-safe policy accepts source metadata only. Do not include real client narratives, uploaded legal "
                "documents, account credentials, API keys, passwords, or raw model responses in source freshness "
                "records."
            ),
            "validation_commands": [
                "python -m pytest tests/test_legal_source_freshness_policy.py -q",
                "rg -n \"(s[k]-[A-Za-z0-9]{20,}|APP_AI_KEY=s[k]-)\" app/backend/services/legal_source_freshness_policy.py docs/LEGAL_SOURCE_FRESHNESS_POLICY.md",
            ],
        }

    def _source_items(self, sources: list[dict[str, Any]] | None) -> list[LegalSourceMetadata]:
        if not sources:
            return list(DEFAULT_SOURCES)
        return [self._coerce_source(index, source) for index, source in enumerate(sources, start=1)]

    def _coerce_source(self, index: int, source: dict[str, Any]) -> LegalSourceMetadata:
        def value(name: str, fallback: str = "") -> str:
            return self._sanitize(str(source.get(name) or fallback))

        return LegalSourceMetadata(
            id=value("id", f"source-{index}"),
            title=value("title", "Untitled source"),
            source_type=value("source_type", "unknown").lower(),
            jurisdiction=value("jurisdiction"),
            effective_date=value("effective_date"),
            last_verified_at=value("last_verified_at"),
            citation=value("citation"),
            use_case=value("use_case", "general_legal_reference"),
        )

    def _review_source(self, source: LegalSourceMetadata, reference_date: date) -> dict[str, Any]:
        flags: list[str] = []
        actions: list[str] = []
        parsed_effective = self._parse_date(source.effective_date)
        parsed_verified = self._parse_date(source.last_verified_at)

        if source.source_type not in FRESHNESS_WINDOWS_DAYS:
            flags.append("unknown_source_type")
            actions.append("Map the source type before it can be used for automated legal retrieval.")

        if not source.jurisdiction:
            flags.append("missing_jurisdiction")
            actions.append("Attach a jurisdiction tag before retrieval or generation.")
        elif source.jurisdiction not in SUPPORTED_JURISDICTIONS:
            flags.append("unsupported_jurisdiction")
            actions.append("Route this source to manual jurisdiction review.")

        if not parsed_effective:
            flags.append("missing_effective_date")
            actions.append("Add an effective date or mark the source as manually verified.")
        elif parsed_effective > reference_date:
            flags.append("future_effective_date")
            actions.append("Do not cite this source until its effective date has arrived.")

        if not source.citation:
            flags.append("missing_citation")
            actions.append("Add a stable citation before using the source in generated legal output.")

        if not parsed_verified:
            flags.append("missing_last_verified_at")
            actions.append("Verify the source before adding it to the retrieval set.")
            days_since_verified = None
        else:
            days_since_verified = (reference_date - parsed_verified).days
            allowed_days = FRESHNESS_WINDOWS_DAYS.get(source.source_type, 0)
            if allowed_days and days_since_verified > allowed_days:
                flags.append("stale_source")
                actions.append("Refresh or replace the source before retrieval.")
            elif allowed_days and days_since_verified > int(allowed_days * 0.75):
                flags.append("freshness_review_due")
                actions.append("Schedule a freshness review before the next release.")

        if any(flag in flags for flag in BLOCKING_FLAGS):
            status = "fail"
        elif flags:
            status = "warn"
        else:
            status = "pass"

        return {
            "id": source.id,
            "title": source.title,
            "source_type": source.source_type,
            "jurisdiction": source.jurisdiction,
            "effective_date": source.effective_date,
            "last_verified_at": source.last_verified_at,
            "citation": source.citation,
            "use_case": source.use_case,
            "days_since_verified": days_since_verified,
            "status": status,
            "flags": flags,
            "recommended_actions": actions or ["Source metadata is ready for retrieval evaluation."],
        }

    def _freshness_rules(self) -> list[dict[str, Any]]:
        return [
            {
                "source_type": source_type,
                "max_days_since_last_verified": max_days,
                "warning_after_days": int(max_days * 0.75),
            }
            for source_type, max_days in sorted(FRESHNESS_WINDOWS_DAYS.items())
        ]

    def _manual_review_escalations(self) -> list[dict[str, str]]:
        return [
            {
                "trigger": "unsupported_jurisdiction",
                "owner": "legal_knowledge_owner",
                "action": "Confirm jurisdiction coverage before source use.",
            },
            {
                "trigger": "stale_source",
                "owner": "legal_review_owner",
                "action": "Refresh the source or block citation in generated output.",
            },
            {
                "trigger": "missing_citation",
                "owner": "legal_review_owner",
                "action": "Attach a stable citation or remove the source from retrieval.",
            },
        ]

    def _recommended_actions(self, failing: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> list[str]:
        if failing:
            return [
                "Block automatic legal answers that depend on failing source metadata.",
                "Refresh stale sources and add jurisdiction, citation, and effective-date fields before release.",
            ]
        if warnings:
            return [
                "Schedule legal source freshness review for warning sources before widening RAG coverage.",
                "Keep generated legal outputs marked review-required while freshness warnings remain.",
            ]
        return [
            "Use these sources in retrieval evaluation with citation and jurisdiction checks enabled.",
            "Re-run freshness review before each release candidate.",
        ]

    def _parse_date(self, value: str) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _sanitize(self, value: str) -> str:
        return SENSITIVE_PATTERN.sub("[redacted]", value).strip()


BLOCKING_FLAGS = {
    "missing_jurisdiction",
    "unsupported_jurisdiction",
    "missing_effective_date",
    "future_effective_date",
    "missing_citation",
    "missing_last_verified_at",
    "stale_source",
    "unknown_source_type",
}


DEFAULT_SOURCES = (
    LegalSourceMetadata(
        id="cn-labor-contract-law",
        title="Synthetic labor contract statute metadata",
        source_type="statute",
        jurisdiction="CN-National",
        effective_date="2013-07-01",
        last_verified_at="2026-03-01",
        citation="Synthetic citation: Labor Contract Law reference",
        use_case="labor_dispute_review",
    ),
    LegalSourceMetadata(
        id="beijing-rent-template",
        title="Synthetic Beijing residential lease template metadata",
        source_type="template",
        jurisdiction="CN-Beijing",
        effective_date="2025-11-15",
        last_verified_at="2026-02-20",
        citation="Synthetic citation: Beijing lease template",
        use_case="lease_document_generation",
    ),
    LegalSourceMetadata(
        id="civil-code-contract-book",
        title="Synthetic civil code contract book metadata",
        source_type="statute",
        jurisdiction="CN-National",
        effective_date="2021-01-01",
        last_verified_at="2026-05-15",
        citation="Synthetic citation: Civil Code contract book",
        use_case="contract_review",
    ),
)
