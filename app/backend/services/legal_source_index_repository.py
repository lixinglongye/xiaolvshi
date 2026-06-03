from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from models.legal_source_index_entries import LegalSourceIndexEntryRecord
from services.legal_source_durable_index_plan import (
    REFERENCE_DATE,
    LegalSourceDurableIndexPlanService,
    LegalSourceIndexEntry,
    LegalSourceMetadataRecord,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


ENTRY_PERSISTENCE_FIELDS = (
    "source_id",
    "index_entry_id",
    "index_version",
    "source_type",
    "jurisdiction",
    "effective_date",
    "citation",
    "citation_key",
    "dedupe_key",
    "freshness_status",
    "freshness_expires_at",
    "metadata_hash",
    "use_case",
    "title",
    "last_verified_at",
    "authority_level",
    "issuer",
    "publication_date",
    "amendment_date",
    "official_url",
    "retrieval_locator",
    "content_hash",
    "ingestion_batch_id",
    "indexed_at",
    "retention_bucket",
    "effective_title_key",
    "content_hash_key",
)


MATCH_FILTERS = (
    "jurisdiction",
    "source_type",
    "freshness_status",
    "authority_level",
    "issuer",
    "use_case",
    "index_version",
    "retention_bucket",
)


class LegalSourceIndexValidationError(ValueError):
    def __init__(self, message: str, validation_report: dict[str, Any]):
        super().__init__(message)
        self.validation_report = validation_report


class LegalSourceIndexRepository:
    def __init__(
        self,
        plan_service: LegalSourceDurableIndexPlanService | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> None:
        self.plan_service = plan_service or LegalSourceDurableIndexPlanService()
        self.reference_date = reference_date

    async def upsert_source_records(
        self,
        db: AsyncSession,
        records: Iterable[dict[str, Any] | LegalSourceMetadataRecord],
    ) -> list[LegalSourceIndexEntryRecord]:
        source_records = list(records)
        entries = self.plan_service.build_index_entries(source_records, self.reference_date)
        validation_report = self.plan_service.validate_index_entries(entries, source_records, self.reference_date)
        if validation_report["status"] == "blocked":
            raise LegalSourceIndexValidationError("Legal source index records failed validation.", validation_report)

        persisted: list[LegalSourceIndexEntryRecord] = []
        try:
            for entry, source_record in zip(entries, source_records, strict=True):
                payload = self._payload_from_entry(entry, source_record)
                existing = await self.get_by_source_id(db, entry.source_id)
                if existing is None:
                    existing = LegalSourceIndexEntryRecord(**payload)
                    db.add(existing)
                else:
                    for field, value in payload.items():
                        setattr(existing, field, value)
                persisted.append(existing)

            await db.commit()
            for record in persisted:
                await db.refresh(record)
            return persisted
        except Exception:
            await db.rollback()
            raise

    async def list_entries(
        self,
        db: AsyncSession,
        filters: dict[str, Any] | None = None,
    ) -> list[LegalSourceIndexEntryRecord]:
        query_filters = filters or {}
        validation_report = self.plan_service.validate_query_filters(query_filters)
        if validation_report["status"] == "fail":
            raise LegalSourceIndexValidationError("Legal source index query filters failed validation.", validation_report)

        query = select(LegalSourceIndexEntryRecord)
        for field in MATCH_FILTERS:
            query = self._apply_match_filter(query, field, query_filters.get(field))

        effective_on_or_before = query_filters.get("effective_on_or_before")
        if effective_on_or_before:
            query = query.where(LegalSourceIndexEntryRecord.effective_date <= str(effective_on_or_before))

        last_verified_at_min = query_filters.get("last_verified_at_min")
        if last_verified_at_min:
            query = query.where(LegalSourceIndexEntryRecord.last_verified_at >= str(last_verified_at_min))

        citation = query_filters.get("citation")
        if citation:
            query = self._apply_citation_filter(query, citation)

        query = query.order_by(
            LegalSourceIndexEntryRecord.jurisdiction.asc(),
            LegalSourceIndexEntryRecord.source_type.asc(),
            LegalSourceIndexEntryRecord.source_id.asc(),
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_source_id(
        self,
        db: AsyncSession,
        source_id: str,
    ) -> LegalSourceIndexEntryRecord | None:
        result = await db.execute(
            select(LegalSourceIndexEntryRecord).where(LegalSourceIndexEntryRecord.source_id == source_id)
        )
        return result.scalar_one_or_none()

    def _payload_from_entry(
        self,
        entry: LegalSourceIndexEntry,
        source_record: dict[str, Any] | LegalSourceMetadataRecord,
    ) -> dict[str, str]:
        payload = {field: getattr(entry, field) for field in ENTRY_PERSISTENCE_FIELDS}
        payload["source_title"] = self._source_title(source_record, entry.title)
        return payload

    def _source_title(
        self,
        source_record: dict[str, Any] | LegalSourceMetadataRecord,
        fallback: str,
    ) -> str:
        if isinstance(source_record, LegalSourceMetadataRecord):
            return source_record.title
        if not isinstance(source_record, dict):
            return fallback
        value = source_record.get("source_title") or source_record.get("source_name") or source_record.get("title")
        return str(value or fallback).strip()

    def _apply_match_filter(self, query: Any, field: str, value: Any) -> Any:
        if value is None or value == "":
            return query
        column = getattr(LegalSourceIndexEntryRecord, field)
        if isinstance(value, (list, tuple, set)):
            values = [str(item) for item in value if item is not None and item != ""]
            return query.where(column.in_(values)) if values else query
        return query.where(column == str(value))

    def _apply_citation_filter(self, query: Any, value: Any) -> Any:
        if isinstance(value, (list, tuple, set)):
            values = [str(item) for item in value if item is not None and item != ""]
            return query.where(LegalSourceIndexEntryRecord.citation.in_(values)) if values else query
        citation = str(value)
        if citation.endswith("*"):
            return query.where(LegalSourceIndexEntryRecord.citation.startswith(citation[:-1]))
        return query.where(LegalSourceIndexEntryRecord.citation == citation)
