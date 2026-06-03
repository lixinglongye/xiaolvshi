from __future__ import annotations

from typing import Any

from models.legal_source_index_entries import LegalSourceIndexEntryRecord
from services.legal_rag_evaluation import LegalRagEvaluationService
from services.legal_source_index_repository import LegalSourceIndexRepository
from sqlalchemy.ext.asyncio import AsyncSession


ACTIVE_FRESHNESS_STATUSES = {"fresh", "review_due"}
INACTIVE_FRESHNESS_STATUSES = {"stale", "unknown"}

SAFE_SOURCE_METADATA_FIELDS = (
    "source_id",
    "index_entry_id",
    "index_version",
    "source_type",
    "jurisdiction",
    "effective_date",
    "citation",
    "citation_key",
    "freshness_status",
    "freshness_expires_at",
    "metadata_hash",
    "use_case",
    "title",
    "source_title",
    "last_verified_at",
    "authority_level",
    "issuer",
    "publication_date",
    "amendment_date",
    "official_url",
    "retrieval_locator",
    "retention_bucket",
)


class LegalRagIndexBindingService:
    """Builds metadata-only legal RAG retrieval plans from durable source indexes."""

    def __init__(
        self,
        repository: LegalSourceIndexRepository | None = None,
        evaluation_service: LegalRagEvaluationService | None = None,
    ) -> None:
        self.repository = repository or LegalSourceIndexRepository()
        self.evaluation_service = evaluation_service or LegalRagEvaluationService()

    async def build_retrieval_plan(
        self,
        db: AsyncSession,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = self._normalize_filters(filters or {})
        validation_report = self.repository.plan_service.validate_query_filters(normalized["validation_filters"])
        if validation_report["status"] == "fail":
            return self._blocked_validation_plan(normalized, validation_report)

        candidates = await self.repository.list_entries(db, normalized["candidate_filters"])
        candidates = self._filter_requested_source_ids(candidates, normalized["requested_source_ids"])

        requested_freshness = _set_text(normalized["repository_filters"].get("freshness_status"))
        inactive_freshness_requested = sorted(requested_freshness & INACTIVE_FRESHNESS_STATUSES)
        active_requested_freshness = requested_freshness & ACTIVE_FRESHNESS_STATUSES

        stale_or_unknown = [
            entry for entry in candidates if str(entry.freshness_status or "").strip() not in ACTIVE_FRESHNESS_STATUSES
        ]
        active_candidates = [
            entry for entry in candidates if str(entry.freshness_status or "").strip() in ACTIVE_FRESHNESS_STATUSES
        ]
        if active_requested_freshness:
            active_candidates = [entry for entry in active_candidates if entry.freshness_status in active_requested_freshness]

        selected_source_ids = [entry.source_id for entry in active_candidates]
        selected_source_set = set(selected_source_ids)
        candidate_source_ids = {entry.source_id for entry in candidates}
        missing_requested_source_ids = sorted(set(normalized["requested_source_ids"]) - candidate_source_ids)
        unusable_requested_source_ids = sorted(set(normalized["requested_source_ids"]) - selected_source_set)

        reason_codes = self._reason_codes(
            selected_source_ids=selected_source_ids,
            missing_requested_source_ids=missing_requested_source_ids,
            stale_or_unknown=stale_or_unknown,
            inactive_freshness_requested=inactive_freshness_requested,
            validation_report=validation_report,
        )
        blocked = not selected_source_ids or bool(inactive_freshness_requested)

        return {
            "status": "blocked" if blocked else ("ready_with_warnings" if reason_codes else "ready"),
            "blocked": blocked,
            "reason_codes": reason_codes,
            "filters": normalized["api_filters"],
            "repository_filters": normalized["repository_filters"],
            "selected_source_ids": selected_source_ids,
            "selected_sources": [self._source_metadata(entry) for entry in active_candidates],
            "blocked_source_ids": [entry.source_id for entry in stale_or_unknown],
            "stale_source_ids": [entry.source_id for entry in stale_or_unknown if entry.freshness_status == "stale"],
            "missing_requested_source_ids": missing_requested_source_ids,
            "unusable_requested_source_ids": unusable_requested_source_ids,
            "coverage_counts": {
                "candidate_source_count": len(candidates),
                "selected_source_count": len(selected_source_ids),
                "blocked_source_count": len(stale_or_unknown),
                "stale_source_count": sum(1 for entry in stale_or_unknown if entry.freshness_status == "stale"),
                "requested_source_count": len(normalized["requested_source_ids"]),
                "missing_requested_source_count": len(missing_requested_source_ids),
                "unusable_requested_source_count": len(unusable_requested_source_ids),
            },
            "validation": self._validation_summary(validation_report),
        }

    def evaluate_retrieval(
        self,
        retrieval_plan: dict[str, Any],
        retrieved_source_ids: list[str] | tuple[str, ...] | set[str] | None = None,
        *,
        answer_citation_source_ids: list[str] | tuple[str, ...] | set[str] | None = None,
        verified_claim_count: int = 0,
        total_claim_count: int | None = None,
        unsupported_claims: list[dict[str, Any]] | None = None,
        pii_findings: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        evaluation_input = {
            "expected_source_ids": _list_text(retrieval_plan.get("selected_source_ids")),
            "retrieved_source_ids": _list_text(retrieved_source_ids),
            "answer_citation_source_ids": _list_text(answer_citation_source_ids),
            "verified_claim_count": verified_claim_count,
            "total_claim_count": verified_claim_count if total_claim_count is None else total_claim_count,
            "unsupported_claims": unsupported_claims or [],
            "stale_source_ids": _list_text(retrieval_plan.get("stale_source_ids")),
            "pii_findings": pii_findings or [],
        }
        return {
            "retrieval_plan": {
                "status": retrieval_plan.get("status"),
                "blocked": bool(retrieval_plan.get("blocked")),
                "reason_codes": _list_text(retrieval_plan.get("reason_codes")),
                "selected_source_ids": _list_text(retrieval_plan.get("selected_source_ids")),
                "coverage_counts": retrieval_plan.get("coverage_counts") or {},
            },
            "evaluation_input": evaluation_input,
            "evaluation": self.evaluation_service.evaluate(evaluation_input),
        }

    def _normalize_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        source_type = _first_text(filters.get("source_type"), filters.get("document_type"))
        effective_on = _first_text(filters.get("effective_on_or_before"), filters.get("effective_on"))
        requested_source_ids = _list_text(filters.get("source_ids") or filters.get("source_id"))

        repository_filters: dict[str, Any] = {}
        for field in (
            "jurisdiction",
            "citation",
            "freshness_status",
            "last_verified_at_min",
            "authority_level",
            "issuer",
            "use_case",
            "index_version",
            "retention_bucket",
        ):
            if filters.get(field) not in (None, ""):
                repository_filters[field] = filters[field]
        if source_type:
            repository_filters["source_type"] = source_type
        if effective_on:
            repository_filters["effective_on_or_before"] = effective_on

        validation_filters = {
            key: value
            for key, value in filters.items()
            if key not in {"document_type", "effective_on", "source_ids", "source_id"}
        }
        if source_type:
            validation_filters["source_type"] = source_type
        if effective_on:
            validation_filters["effective_on_or_before"] = effective_on

        candidate_filters = {
            key: value
            for key, value in repository_filters.items()
            if key not in {"freshness_status"}
        }

        return {
            "api_filters": {
                "jurisdiction": _empty_none(filters.get("jurisdiction")),
                "document_type": _empty_none(source_type),
                "effective_on": _empty_none(effective_on),
                "source_ids": requested_source_ids,
                "freshness_status": repository_filters.get("freshness_status", ["fresh", "review_due"]),
                "use_case": _empty_none(filters.get("use_case")),
            },
            "repository_filters": repository_filters,
            "candidate_filters": candidate_filters,
            "validation_filters": validation_filters,
            "requested_source_ids": requested_source_ids,
        }

    def _filter_requested_source_ids(
        self,
        entries: list[LegalSourceIndexEntryRecord],
        requested_source_ids: list[str],
    ) -> list[LegalSourceIndexEntryRecord]:
        if not requested_source_ids:
            return entries
        requested = set(requested_source_ids)
        return [entry for entry in entries if entry.source_id in requested]

    def _reason_codes(
        self,
        *,
        selected_source_ids: list[str],
        missing_requested_source_ids: list[str],
        stale_or_unknown: list[LegalSourceIndexEntryRecord],
        inactive_freshness_requested: list[str],
        validation_report: dict[str, Any],
    ) -> list[str]:
        codes: list[str] = []
        if validation_report.get("warnings"):
            codes.extend(_list_text(validation_report.get("warnings")))
        if inactive_freshness_requested:
            codes.append("inactive_freshness_filter_blocked")
        if stale_or_unknown:
            codes.append("stale_or_unknown_sources_excluded")
        if missing_requested_source_ids:
            codes.append("requested_sources_not_indexed")
        if not selected_source_ids:
            codes.append("no_index_coverage")
        return sorted(set(codes))

    def _blocked_validation_plan(
        self,
        normalized: dict[str, Any],
        validation_report: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": "blocked",
            "blocked": True,
            "reason_codes": sorted(set(_list_text(validation_report.get("failures")) or ["invalid_query_filters"])),
            "filters": normalized["api_filters"],
            "repository_filters": normalized["repository_filters"],
            "selected_source_ids": [],
            "selected_sources": [],
            "blocked_source_ids": [],
            "stale_source_ids": [],
            "missing_requested_source_ids": normalized["requested_source_ids"],
            "unusable_requested_source_ids": normalized["requested_source_ids"],
            "coverage_counts": {
                "candidate_source_count": 0,
                "selected_source_count": 0,
                "blocked_source_count": 0,
                "stale_source_count": 0,
                "requested_source_count": len(normalized["requested_source_ids"]),
                "missing_requested_source_count": len(normalized["requested_source_ids"]),
                "unusable_requested_source_count": len(normalized["requested_source_ids"]),
            },
            "validation": self._validation_summary(validation_report),
        }

    def _validation_summary(self, validation_report: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": validation_report.get("status"),
            "failures": _list_text(validation_report.get("failures")),
            "warnings": _list_text(validation_report.get("warnings")),
            "forbidden_fields_present": _list_text(validation_report.get("forbidden_fields_present")),
            "sensitive_value_findings": [
                {"path": str(item.get("path") or ""), "type": str(item.get("type") or "")}
                for item in validation_report.get("sensitive_value_findings", [])
                if isinstance(item, dict)
            ],
            "active_index_query_safe": bool(validation_report.get("active_index_query_safe")),
        }

    def _source_metadata(self, entry: LegalSourceIndexEntryRecord) -> dict[str, str]:
        return {field: str(getattr(entry, field) or "") for field in SAFE_SOURCE_METADATA_FIELDS}


def _first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _empty_none(value: Any) -> Any:
    return value if value not in ("", None) else None


def _list_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [text for text in (str(item or "").strip() for item in value) if text]
    text = str(value or "").strip()
    return [text] if text else []


def _set_text(value: Any) -> set[str]:
    return set(_list_text(value))
