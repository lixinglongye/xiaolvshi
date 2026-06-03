from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
import hashlib
import json
import re
from typing import Any, Iterable


REFERENCE_DATE = date(2026, 6, 4)
SCHEMA_VERSION = "legal-source-durable-index-plan-v1"
INDEX_VERSION = "legal-source-metadata-index-v1"

SUPPORTED_JURISDICTIONS = {
    "CN",
    "CN-National",
    "CN-Beijing",
    "CN-Shanghai",
    "CN-Guangdong",
    "CN-Zhejiang",
    "CN-Jiangsu",
}

SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS = {
    "statute": 365,
    "regulation": 365,
    "judicial_interpretation": 365,
    "case": 730,
    "template": 365,
    "internal_note": 180,
}

REQUIRED_SOURCE_RECORD_FIELDS = (
    "id",
    "title",
    "source_type",
    "jurisdiction",
    "effective_date",
    "citation",
    "last_verified_at",
)

OPTIONAL_SOURCE_RECORD_FIELDS = (
    "authority_level",
    "issuer",
    "publication_date",
    "amendment_date",
    "official_url",
    "retrieval_locator",
    "content_hash",
    "use_case",
    "ingestion_batch_id",
)

REQUIRED_INDEX_ENTRY_FIELDS = (
    "index_entry_id",
    "source_id",
    "title",
    "source_type",
    "jurisdiction",
    "effective_date",
    "citation",
    "last_verified_at",
    "freshness_status",
    "freshness_expires_at",
    "dedupe_key",
    "metadata_hash",
    "index_version",
)

OPTIONAL_INDEX_ENTRY_FIELDS = (
    "authority_level",
    "issuer",
    "publication_date",
    "amendment_date",
    "official_url",
    "retrieval_locator",
    "content_hash",
    "use_case",
    "ingestion_batch_id",
    "indexed_at",
    "retention_bucket",
    "citation_key",
    "effective_title_key",
    "content_hash_key",
)

FORBIDDEN_RAW_TEXT_FIELDS = (
    "raw_text",
    "full_text",
    "document_body",
    "source_body",
    "law_text",
    "article_text",
    "text",
    "body",
    "content",
    "html",
    "markdown",
    "pdf_bytes",
    "base64_pdf",
    "ocr_text",
    "chunk_text",
    "chunk_body",
    "excerpt",
    "snippet",
    "embedding",
    "embedding_vector",
    "vector",
    "dense_vector",
    "sparse_vector",
)

FORBIDDEN_PRIVATE_OR_RUNTIME_FIELDS = (
    "client_name",
    "client_email",
    "client_phone",
    "phone",
    "email",
    "personal_id",
    "case_number",
    "matter_id",
    "prompt",
    "raw_prompt",
    "model_response",
    "raw_model_output",
    "request_body",
    "response_body",
    "headers",
    "authorization",
    "api_key",
    "password",
    "secret",
    "access_token",
    "refresh_token",
)

FORBIDDEN_FIELDS = FORBIDDEN_RAW_TEXT_FIELDS + FORBIDDEN_PRIVATE_OR_RUNTIME_FIELDS

ALLOWED_QUERY_FILTERS = (
    "jurisdiction",
    "source_type",
    "effective_on_or_before",
    "citation",
    "freshness_status",
    "last_verified_at_min",
    "authority_level",
    "issuer",
    "use_case",
    "index_version",
    "retention_bucket",
)

FRESHNESS_STATUSES = {"fresh", "review_due", "stale", "unknown"}
ACTIVE_QUERY_FRESHNESS_STATUSES = {"fresh", "review_due"}

SENSITIVE_VALUE_PATTERNS = (
    ("api_key_like", re.compile(r"\bs[k]-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE)),
    ("bearer_token_like", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{12,}\b", re.IGNORECASE)),
    ("email_like", re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b")),
    ("credential_marker", re.compile(r"\b(password|secret|api[_-]?key|authorization)\b", re.IGNORECASE)),
)

NON_KEY_CHARS = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class LegalSourceMetadataRecord:
    id: str
    title: str
    source_type: str
    jurisdiction: str
    effective_date: str
    citation: str
    last_verified_at: str
    authority_level: str = ""
    issuer: str = ""
    publication_date: str = ""
    amendment_date: str = ""
    official_url: str = ""
    retrieval_locator: str = ""
    content_hash: str = ""
    use_case: str = "general_legal_reference"
    ingestion_batch_id: str = ""

    def to_api(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class LegalSourceIndexEntry:
    index_entry_id: str
    source_id: str
    title: str
    source_type: str
    jurisdiction: str
    effective_date: str
    citation: str
    last_verified_at: str
    freshness_status: str
    freshness_expires_at: str
    dedupe_key: str
    metadata_hash: str
    index_version: str = INDEX_VERSION
    authority_level: str = ""
    issuer: str = ""
    publication_date: str = ""
    amendment_date: str = ""
    official_url: str = ""
    retrieval_locator: str = ""
    content_hash: str = ""
    use_case: str = "general_legal_reference"
    ingestion_batch_id: str = ""
    indexed_at: str = REFERENCE_DATE.isoformat()
    retention_bucket: str = "active_metadata"
    citation_key: str = ""
    effective_title_key: str = ""
    content_hash_key: str = ""

    def to_api(self) -> dict[str, str]:
        return asdict(self)


class LegalSourceDurableIndexPlanService:
    """Plan and validate a local durable legal-source metadata index."""

    def build_plan(
        self,
        source_records: Iterable[dict[str, Any] | LegalSourceMetadataRecord] | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> dict[str, Any]:
        raw_source_records = list(source_records) if source_records is not None else None
        source_items = self._source_items(raw_source_records)
        index_entries = self.build_index_entries(source_items, reference_date)
        sample_validation = self.validate_index_entries(
            index_entries,
            raw_source_records if raw_source_records is not None else source_items,
            reference_date,
        )
        query_filter_validation = self.validate_query_filters(
            {
                "jurisdiction": "CN-National",
                "source_type": "statute",
                "effective_on_or_before": reference_date.isoformat(),
                "freshness_status": ["fresh", "review_due"],
            }
        )

        return {
            "schema_version": SCHEMA_VERSION,
            "status": sample_validation["status"],
            "source_record_contract": self._source_record_contract(),
            "index_entry_schema": self._index_entry_schema(),
            "jurisdiction_fields": self._jurisdiction_fields(),
            "effective_date_fields": self._effective_date_fields(),
            "citation_fields": self._citation_fields(),
            "freshness_fields": self._freshness_fields(),
            "dedupe_fields": self._dedupe_fields(),
            "query_filters": self._query_filter_definitions(),
            "retention_policy": self._retention_policy(),
            "rebuild_policy": self._rebuild_policy(),
            "forbidden_fields": self._forbidden_field_definitions(),
            "sample_source_records": [record.to_api() for record in source_items],
            "sample_index_entries": [entry.to_api() for entry in index_entries],
            "sample_validation": sample_validation,
            "sample_query_filter_validation": query_filter_validation,
            "local_only_guards": {
                "database_required": False,
                "vector_store_required": False,
                "network_required": False,
                "raw_text_storage_allowed": False,
                "router_integration_required": False,
                "release_or_ledger_integration_required": False,
            },
            "privacy_note": (
                "Durable index entries are metadata-only. They must not contain raw legal source text, extracted "
                "chunks, embeddings, client identifiers, prompts, model responses, credentials, or request payloads."
            ),
            "integration_note": (
                "This service is intentionally local and standalone. It defines a future durable-index contract "
                "without modifying ingestion, freshness, router, release, or ledger services."
            ),
            "validation_commands": [
                "python -m pytest tests/test_legal_source_durable_index_plan.py -q",
                "python -m compileall services/legal_source_durable_index_plan.py",
            ],
        }

    def build_policy(
        self,
        source_records: Iterable[dict[str, Any] | LegalSourceMetadataRecord] | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> dict[str, Any]:
        return self.build_plan(source_records, reference_date)

    def build_index_entries(
        self,
        source_records: Iterable[dict[str, Any] | LegalSourceMetadataRecord] | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> list[LegalSourceIndexEntry]:
        entries: list[LegalSourceIndexEntry] = []
        for record in self._source_items(source_records):
            entries.append(self._index_entry_from_source(record, reference_date))
        return entries

    def validate_index_entries(
        self,
        entries: Iterable[dict[str, Any] | LegalSourceIndexEntry] | None = None,
        source_records: Iterable[dict[str, Any] | LegalSourceMetadataRecord] | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> dict[str, Any]:
        entry_items = self._entry_items(entries, reference_date)
        source_raw_by_id = self._source_raw_by_id(source_records)
        duplicate_entry_ids = self._duplicates(entry.index_entry_id for entry in entry_items)
        duplicate_dedupe_keys = self._duplicates(entry.dedupe_key for entry in entry_items if entry.dedupe_key)
        reviews = [
            self._review_index_entry(
                entry=entry,
                raw_entry=self._raw_entry(raw_entries=entries, index=index, fallback=entry),
                source_raw=source_raw_by_id.get(entry.source_id, {}),
                duplicate_entry_ids=duplicate_entry_ids,
                duplicate_dedupe_keys=duplicate_dedupe_keys,
                reference_date=reference_date,
            )
            for index, entry in enumerate(entry_items)
        ]

        failing = [review for review in reviews if review["status"] == "fail"]
        warnings = [review for review in reviews if review["status"] == "warn"]
        return {
            "status": "blocked" if failing else ("review_recommended" if warnings else "ready"),
            "summary": {
                "entry_count": len(reviews),
                "ready_count": sum(1 for review in reviews if review["status"] == "pass"),
                "warning_count": len(warnings),
                "blocked_count": len(failing),
                "duplicate_index_entry_ids": sorted(duplicate_entry_ids),
                "duplicate_dedupe_keys": sorted(duplicate_dedupe_keys),
                "forbidden_field_entry_ids": [
                    review["index_entry_id"] for review in reviews if "forbidden_field_present" in review["flags"]
                ],
                "stale_entry_ids": [
                    review["index_entry_id"] for review in reviews if "stale_freshness_metadata" in review["flags"]
                ],
                "reference_date": reference_date.isoformat(),
                "raw_text_storage_allowed": False,
            },
            "entry_reviews": reviews,
            "recommended_actions": self._recommended_actions(failing, warnings),
        }

    def validate_query_filters(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        raw_filters = filters if isinstance(filters, dict) else {}
        forbidden_fields = sorted(self._forbidden_keys(raw_filters))
        sensitive_findings = self._sensitive_value_findings(raw_filters)
        unknown_filters = sorted(set(raw_filters) - set(ALLOWED_QUERY_FILTERS))
        failures: list[str] = []
        warnings: list[str] = []

        if forbidden_fields:
            failures.append("forbidden_query_filter_present")
        if sensitive_findings:
            failures.append("sensitive_query_filter_value_present")
        if unknown_filters:
            warnings.append("unknown_query_filter")

        jurisdiction = raw_filters.get("jurisdiction")
        if jurisdiction and not self._all_values_allowed(jurisdiction, SUPPORTED_JURISDICTIONS):
            failures.append("unsupported_jurisdiction_filter")

        source_type = raw_filters.get("source_type")
        if source_type and not self._all_values_allowed(source_type, set(SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS)):
            failures.append("unsupported_source_type_filter")

        effective_on_or_before = raw_filters.get("effective_on_or_before")
        if effective_on_or_before and self._parse_date(str(effective_on_or_before)) is None:
            failures.append("invalid_effective_filter_date")

        verified_after = raw_filters.get("last_verified_at_min")
        if verified_after and self._parse_date(str(verified_after)) is None:
            failures.append("invalid_verified_filter_date")

        freshness_status = raw_filters.get("freshness_status")
        if freshness_status and not self._all_values_allowed(freshness_status, FRESHNESS_STATUSES):
            failures.append("unsupported_freshness_status_filter")
        elif freshness_status and not self._all_values_allowed(freshness_status, ACTIVE_QUERY_FRESHNESS_STATUSES):
            warnings.append("stale_or_unknown_freshness_filter")

        status = "fail" if failures else ("warn" if warnings else "pass")
        return {
            "status": status,
            "allowed_filters": list(ALLOWED_QUERY_FILTERS),
            "unknown_filters": unknown_filters,
            "forbidden_fields_present": forbidden_fields,
            "sensitive_value_findings": sensitive_findings,
            "warnings": warnings,
            "failures": failures,
            "active_index_query_safe": status != "fail",
        }

    def _index_entry_from_source(
        self,
        source: LegalSourceMetadataRecord,
        reference_date: date,
    ) -> LegalSourceIndexEntry:
        citation_key = "|".join(
            part
            for part in (
                self._canonical(source.source_type),
                self._canonical(source.jurisdiction),
                self._canonical(source.citation),
            )
            if part
        )
        effective_title_key = "|".join(
            part
            for part in (
                self._canonical(source.source_type),
                self._canonical(source.jurisdiction),
                self._canonical(source.title),
                source.effective_date,
            )
            if part
        )
        content_hash_key = self._canonical(source.content_hash)
        dedupe_key = content_hash_key or citation_key or effective_title_key
        freshness = self._freshness_snapshot(source.source_type, source.last_verified_at, reference_date)
        metadata_hash = self._metadata_hash(source)
        source_slug = self._canonical(source.id) or "missing-source-id"
        return LegalSourceIndexEntry(
            index_entry_id=f"idx-{source_slug}-{metadata_hash[:12]}",
            source_id=source.id,
            title=source.title,
            source_type=source.source_type,
            jurisdiction=source.jurisdiction,
            effective_date=source.effective_date,
            citation=source.citation,
            last_verified_at=source.last_verified_at,
            freshness_status=freshness["status"],
            freshness_expires_at=freshness["expires_at"],
            dedupe_key=dedupe_key,
            metadata_hash=f"sha256:{metadata_hash}",
            authority_level=source.authority_level,
            issuer=source.issuer,
            publication_date=source.publication_date,
            amendment_date=source.amendment_date,
            official_url=source.official_url,
            retrieval_locator=source.retrieval_locator,
            content_hash=source.content_hash,
            use_case=source.use_case,
            ingestion_batch_id=source.ingestion_batch_id,
            indexed_at=reference_date.isoformat(),
            retention_bucket="active_metadata"
            if freshness["status"] in ACTIVE_QUERY_FRESHNESS_STATUSES
            else "metadata_review",
            citation_key=citation_key,
            effective_title_key=effective_title_key,
            content_hash_key=content_hash_key,
        )

    def _review_index_entry(
        self,
        *,
        entry: LegalSourceIndexEntry,
        raw_entry: dict[str, Any],
        source_raw: dict[str, Any],
        duplicate_entry_ids: set[str],
        duplicate_dedupe_keys: set[str],
        reference_date: date,
    ) -> dict[str, Any]:
        flags: list[str] = []
        actions: list[str] = []
        raw_combined = {"entry": raw_entry, "source_record": source_raw}
        missing_required = [field for field in REQUIRED_INDEX_ENTRY_FIELDS if not getattr(entry, field)]
        forbidden_present = sorted(self._forbidden_keys(raw_combined))
        sensitive_findings = self._sensitive_value_findings(raw_combined)
        unknown_fields = sorted(set(raw_entry) - set(REQUIRED_INDEX_ENTRY_FIELDS + OPTIONAL_INDEX_ENTRY_FIELDS))
        parsed_effective = self._parse_date(entry.effective_date)
        parsed_verified = self._parse_date(entry.last_verified_at)
        parsed_expires = self._parse_date(entry.freshness_expires_at)
        expected_freshness = self._freshness_snapshot(entry.source_type, entry.last_verified_at, reference_date)
        expected_keys = self._expected_dedupe_fields(entry)

        if missing_required:
            flags.append("missing_required_index_field")
            actions.append("Populate every required durable index metadata field before persistence.")

        if forbidden_present:
            flags.append("forbidden_field_present")
            actions.append("Remove raw text, embeddings, client data, prompts, model output, or credential fields.")

        if sensitive_findings:
            flags.append("sensitive_value_present")
            actions.append("Redact credential-like or contact-like values before building the durable index.")

        if unknown_fields:
            flags.append("unknown_index_field")
            actions.append("Review unknown fields and either add them to the schema or remove them before persistence.")

        if entry.index_entry_id in duplicate_entry_ids:
            flags.append("duplicate_index_entry_id")
            actions.append("Regenerate a stable unique index_entry_id for each source metadata version.")

        if entry.dedupe_key in duplicate_dedupe_keys:
            flags.append("duplicate_dedupe_key")
            actions.append("Select one canonical source metadata entry before durable indexing.")

        if entry.source_type and entry.source_type not in SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS:
            flags.append("unknown_source_type")
            actions.append("Map source_type to a known freshness window before indexing.")

        if entry.jurisdiction and entry.jurisdiction not in SUPPORTED_JURISDICTIONS:
            flags.append("unsupported_jurisdiction")
            actions.append("Route unsupported jurisdiction metadata to manual legal source review.")

        if entry.effective_date and parsed_effective is None:
            flags.append("invalid_effective_date")
            actions.append("Use ISO date format YYYY-MM-DD for effective_date.")
        elif parsed_effective and parsed_effective > reference_date:
            flags.append("future_effective_date")
            actions.append("Do not place not-yet-effective sources in the active durable index.")

        if entry.last_verified_at and parsed_verified is None:
            flags.append("invalid_last_verified_at")
            actions.append("Use ISO date format YYYY-MM-DD for last_verified_at.")

        if entry.freshness_status not in FRESHNESS_STATUSES:
            flags.append("invalid_freshness_status")
            actions.append("Use one of fresh, review_due, stale, or unknown for freshness_status.")
        elif entry.freshness_status != expected_freshness["status"]:
            flags.append("freshness_status_mismatch")
            actions.append("Recompute freshness_status from source_type and last_verified_at.")

        if entry.freshness_status == "stale":
            flags.append("stale_freshness_metadata")
            actions.append("Retain stale entries only for audit or rebuild; exclude them from active retrieval.")
        elif entry.freshness_status == "review_due":
            flags.append("freshness_review_due")
            actions.append("Schedule source verification before expanding active retrieval coverage.")

        if entry.freshness_expires_at and parsed_expires is None:
            flags.append("invalid_freshness_expires_at")
            actions.append("Use ISO date format YYYY-MM-DD for freshness_expires_at.")
        elif parsed_expires and expected_freshness["expires_at"] and entry.freshness_expires_at != expected_freshness["expires_at"]:
            flags.append("freshness_expires_at_mismatch")
            actions.append("Recompute freshness_expires_at from last_verified_at and the source-type window.")

        for field_name in ("publication_date", "amendment_date", "indexed_at"):
            raw_value = getattr(entry, field_name)
            if raw_value and self._parse_date(raw_value) is None:
                flags.append(f"invalid_{field_name}")
                actions.append(f"Use ISO date format YYYY-MM-DD for {field_name}.")

        for key_name, expected_value in expected_keys.items():
            actual_value = getattr(entry, key_name)
            if actual_value and actual_value != expected_value:
                flags.append(f"{key_name}_mismatch")
                actions.append(f"Recompute {key_name} from metadata-only source fields.")

        if entry.dedupe_key and entry.dedupe_key not in {
            expected_keys["content_hash_key"],
            expected_keys["citation_key"],
            expected_keys["effective_title_key"],
        }:
            flags.append("dedupe_key_mismatch")
            actions.append("Set dedupe_key to content_hash_key, citation_key, or effective_title_key.")

        if entry.citation and len(entry.citation) < 8:
            flags.append("weak_citation")
            actions.append("Use a stable citation that a legal reviewer can trace.")

        if any(flag in flags for flag in BLOCKING_FLAGS):
            status = "fail"
        elif flags:
            status = "warn"
        else:
            status = "pass"

        return {
            "index_entry_id": entry.index_entry_id,
            "source_id": entry.source_id,
            "source_type": entry.source_type,
            "jurisdiction": entry.jurisdiction,
            "effective_date": entry.effective_date,
            "citation": entry.citation,
            "freshness_status": entry.freshness_status,
            "dedupe_key": entry.dedupe_key,
            "missing_required_fields": missing_required,
            "unknown_fields": unknown_fields,
            "forbidden_fields_present": forbidden_present,
            "sensitive_value_findings": sensitive_findings,
            "status": status,
            "flags": flags,
            "allowed_for_active_index": status != "fail",
            "recommended_actions": actions or ["Index entry is ready for metadata-only durable indexing."],
        }

    def _source_record_contract(self) -> dict[str, Any]:
        return {
            "type": "object",
            "required_fields": list(REQUIRED_SOURCE_RECORD_FIELDS),
            "optional_metadata_fields": list(OPTIONAL_SOURCE_RECORD_FIELDS),
            "allowed_fields": list(REQUIRED_SOURCE_RECORD_FIELDS + OPTIONAL_SOURCE_RECORD_FIELDS),
            "notes": [
                "Source records are metadata-only inputs for durable index entry generation.",
                "Raw legal text, chunks, embeddings, prompts, client facts, and credentials are forbidden.",
            ],
        }

    def _index_entry_schema(self) -> dict[str, Any]:
        fields = []
        for name in REQUIRED_INDEX_ENTRY_FIELDS:
            fields.append(self._field_definition(name, required=True))
        for name in OPTIONAL_INDEX_ENTRY_FIELDS:
            fields.append(self._field_definition(name, required=False))
        return {
            "type": "object",
            "required_fields": list(REQUIRED_INDEX_ENTRY_FIELDS),
            "optional_metadata_fields": list(OPTIONAL_INDEX_ENTRY_FIELDS),
            "allowed_fields": list(REQUIRED_INDEX_ENTRY_FIELDS + OPTIONAL_INDEX_ENTRY_FIELDS),
            "fields": fields,
        }

    def _field_definition(self, name: str, required: bool) -> dict[str, Any]:
        descriptions = {
            "index_entry_id": "Stable durable index entry id for a specific source metadata version.",
            "source_id": "Stable local source metadata id.",
            "title": "Reviewer-readable source title; not the raw source body.",
            "source_type": "One of statute, regulation, judicial_interpretation, case, template, or internal_note.",
            "jurisdiction": "Jurisdiction filter used to prevent cross-jurisdiction retrieval drift.",
            "effective_date": "Legal effective date in YYYY-MM-DD format.",
            "citation": "Stable reviewer-checkable citation.",
            "last_verified_at": "Local verification date in YYYY-MM-DD format.",
            "freshness_status": "Computed freshness status: fresh, review_due, stale, or unknown.",
            "freshness_expires_at": "Date when the source exits its freshness window.",
            "dedupe_key": "Canonical dedupe key selected from content_hash_key, citation_key, or effective_title_key.",
            "metadata_hash": "Hash of metadata-only fields used for rebuild diffing.",
            "index_version": "Local durable index schema version.",
            "authority_level": "Optional authority rank such as national_statute or local_regulation.",
            "issuer": "Optional public issuer name.",
            "publication_date": "Optional publication date in YYYY-MM-DD format.",
            "amendment_date": "Optional latest amendment date in YYYY-MM-DD format.",
            "official_url": "Optional public locator; this service never fetches it.",
            "retrieval_locator": "Optional local locator that must not contain raw legal text.",
            "content_hash": "Optional precomputed body hash supplied by ingestion, not the body itself.",
            "use_case": "Optional local use-case label.",
            "ingestion_batch_id": "Optional local batch id.",
            "indexed_at": "Date this metadata entry was materialized locally.",
            "retention_bucket": "Metadata lifecycle bucket such as active_metadata or metadata_review.",
            "citation_key": "Dedupe helper derived from source_type, jurisdiction, and citation.",
            "effective_title_key": "Dedupe helper derived from source_type, jurisdiction, title, and effective_date.",
            "content_hash_key": "Dedupe helper derived from content_hash only.",
        }
        return {
            "name": name,
            "type": "string",
            "required": required,
            "description": descriptions[name],
        }

    def _jurisdiction_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "jurisdiction",
                "required": True,
                "allowed_values": sorted(SUPPORTED_JURISDICTIONS),
                "query_filter": True,
                "purpose": "Restrict retrieval candidates to the user's legal jurisdiction.",
            }
        ]

    def _effective_date_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "effective_date",
                "required": True,
                "format": "YYYY-MM-DD",
                "query_filter": "effective_on_or_before",
                "purpose": "Exclude sources that were not effective on the requested legal date.",
            },
            {
                "name": "publication_date",
                "required": False,
                "format": "YYYY-MM-DD",
                "purpose": "Reviewer context only; not a substitute for effective_date.",
            },
            {
                "name": "amendment_date",
                "required": False,
                "format": "YYYY-MM-DD",
                "purpose": "Records latest known amendment metadata without storing amendment text.",
            },
        ]

    def _citation_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "citation",
                "required": True,
                "query_filter": True,
                "purpose": "Reviewer traceability and exact citation lookup.",
            },
            {
                "name": "official_url",
                "required": False,
                "purpose": "Manual locator only; no network fetch is performed.",
            },
            {
                "name": "retrieval_locator",
                "required": False,
                "purpose": "Local pointer to retrieval material managed outside this metadata plan.",
            },
        ]

    def _freshness_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "last_verified_at",
                "required": True,
                "format": "YYYY-MM-DD",
                "purpose": "Input date for freshness status and expiry calculation.",
            },
            {
                "name": "freshness_status",
                "required": True,
                "allowed_values": sorted(FRESHNESS_STATUSES),
                "active_query_values": sorted(ACTIVE_QUERY_FRESHNESS_STATUSES),
                "purpose": "Allows active queries to exclude stale or unknown metadata.",
            },
            {
                "name": "freshness_expires_at",
                "required": True,
                "format": "YYYY-MM-DD",
                "purpose": "Next date requiring source review or rebuild exclusion.",
            },
            {
                "name": "source_type",
                "required": True,
                "windows_days": dict(sorted(SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS.items())),
                "purpose": "Selects the local freshness window.",
            },
        ]

    def _dedupe_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "dedupe_key",
                "required": True,
                "purpose": "Canonical active dedupe selector for durable index writes.",
            },
            {
                "name": "citation_key",
                "fields": ["source_type", "jurisdiction", "citation"],
                "purpose": "Detects duplicate canonical citations.",
            },
            {
                "name": "effective_title_key",
                "fields": ["source_type", "jurisdiction", "title", "effective_date"],
                "purpose": "Detects duplicate source versions when citation formatting differs.",
            },
            {
                "name": "content_hash_key",
                "fields": ["content_hash"],
                "purpose": "Optional exact fingerprint dedupe without storing source content.",
            },
            {
                "name": "metadata_hash",
                "fields": list(REQUIRED_SOURCE_RECORD_FIELDS + OPTIONAL_SOURCE_RECORD_FIELDS),
                "purpose": "Detects metadata changes for incremental rebuild planning.",
            },
        ]

    def _query_filter_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "jurisdiction",
                "operators": ["equals", "in"],
                "required_for_active_retrieval": True,
                "allowed_values": sorted(SUPPORTED_JURISDICTIONS),
            },
            {
                "name": "source_type",
                "operators": ["equals", "in"],
                "allowed_values": sorted(SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS),
            },
            {
                "name": "effective_on_or_before",
                "operators": ["less_than_or_equal"],
                "field": "effective_date",
                "format": "YYYY-MM-DD",
            },
            {
                "name": "freshness_status",
                "operators": ["in"],
                "active_query_values": sorted(ACTIVE_QUERY_FRESHNESS_STATUSES),
            },
            {
                "name": "last_verified_at_min",
                "operators": ["greater_than_or_equal"],
                "field": "last_verified_at",
                "format": "YYYY-MM-DD",
            },
            {"name": "citation", "operators": ["equals", "prefix"]},
            {"name": "authority_level", "operators": ["equals", "in"]},
            {"name": "issuer", "operators": ["equals"]},
            {"name": "use_case", "operators": ["equals", "in"]},
            {"name": "index_version", "operators": ["equals"]},
            {"name": "retention_bucket", "operators": ["equals", "in"]},
        ]

    def _retention_policy(self) -> dict[str, Any]:
        return {
            "raw_text_retention": "never_store",
            "active_metadata_entries": "retain_while_source_is_supported_and_fresh",
            "review_due_metadata_entries": "retain_but_mark_review_required_until_refreshed",
            "stale_metadata_entries": "exclude_from_active_retrieval_keep_180_days_for_rebuild_audit",
            "superseded_metadata_versions": "keep_400_days_for_release_diff_and_rebuild_rollback",
            "dedupe_tombstones": "keep_730_days_to_prevent_reintroduction_of_duplicate_sources",
            "rejected_entries": "delete_immediately_after_validation_report",
            "deletion_triggers": [
                "source metadata removed by legal knowledge owner",
                "unsupported jurisdiction or source type",
                "forbidden raw text or private data field detected",
                "freshness window exceeded without re-verification",
            ],
        }

    def _rebuild_policy(self) -> dict[str, Any]:
        return {
            "rebuild_mode": "deterministic_local_metadata_rebuild",
            "full_rebuild_triggers": [
                "schema_version_change",
                "index_version_change",
                "jurisdiction_taxonomy_change",
                "source_type_freshness_window_change",
                "dedupe_algorithm_change",
                "forbidden_field_policy_change",
            ],
            "incremental_rebuild_triggers": [
                "source metadata_hash changed",
                "last_verified_at changed",
                "citation changed",
                "effective_date changed",
                "content_hash changed",
                "retention_bucket changed",
            ],
            "rebuild_inputs": [
                "metadata-only source records",
                "local schema constants",
                "reference_date",
            ],
            "rebuild_outputs": [
                "metadata-only durable index entries",
                "validation report",
                "dedupe quarantine list",
            ],
            "prohibited_rebuild_inputs": list(FORBIDDEN_FIELDS),
            "external_services_required": [],
        }

    def _forbidden_field_definitions(self) -> list[dict[str, str]]:
        return [
            {
                "name": field,
                "reason": "Durable legal-source index entries store metadata only; raw text, vectors, private data, prompts, model output, and credentials are forbidden.",
            }
            for field in FORBIDDEN_FIELDS
        ]

    def _recommended_actions(
        self,
        failing: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> list[str]:
        if failing:
            return [
                "Block failing index entries from durable active retrieval until metadata is corrected.",
                "Remove forbidden raw text, vector, private matter, prompt, model-output, or credential fields.",
                "Quarantine duplicate dedupe keys and keep one canonical metadata entry.",
            ]
        if warnings:
            return [
                "Review warning entries before release expansion, especially review-due freshness or weak citations.",
                "Keep warning entries marked review-required in active metadata filters.",
            ]
        return [
            "Use the validated entries as metadata-only durable index candidates.",
            "Rebuild deterministically from source metadata when schema, freshness, or dedupe policy changes.",
        ]

    def _source_items(
        self,
        source_records: Iterable[dict[str, Any] | LegalSourceMetadataRecord] | None,
    ) -> list[LegalSourceMetadataRecord]:
        if source_records is None:
            return list(DEFAULT_SOURCE_RECORDS)
        items: list[LegalSourceMetadataRecord] = []
        for item in source_records:
            if isinstance(item, LegalSourceMetadataRecord):
                items.append(item)
            elif isinstance(item, dict):
                items.append(self._coerce_source(item))
        return items

    def _coerce_source(self, source: dict[str, Any]) -> LegalSourceMetadataRecord:
        def value(name: str, fallback: str = "") -> str:
            return self._sanitize(str(source.get(name) or fallback))

        return LegalSourceMetadataRecord(
            id=value("id"),
            title=value("title"),
            source_type=value("source_type").lower(),
            jurisdiction=value("jurisdiction"),
            effective_date=value("effective_date"),
            citation=value("citation"),
            last_verified_at=value("last_verified_at"),
            authority_level=value("authority_level"),
            issuer=value("issuer"),
            publication_date=value("publication_date"),
            amendment_date=value("amendment_date"),
            official_url=value("official_url"),
            retrieval_locator=value("retrieval_locator"),
            content_hash=value("content_hash"),
            use_case=value("use_case", "general_legal_reference"),
            ingestion_batch_id=value("ingestion_batch_id"),
        )

    def _entry_items(
        self,
        entries: Iterable[dict[str, Any] | LegalSourceIndexEntry] | None,
        reference_date: date,
    ) -> list[LegalSourceIndexEntry]:
        if entries is None:
            return self.build_index_entries(DEFAULT_SOURCE_RECORDS, reference_date)
        items: list[LegalSourceIndexEntry] = []
        for item in entries:
            if isinstance(item, LegalSourceIndexEntry):
                items.append(item)
            elif isinstance(item, dict):
                items.append(self._coerce_entry(item))
        return items

    def _coerce_entry(self, entry: dict[str, Any]) -> LegalSourceIndexEntry:
        def value(name: str, fallback: str = "") -> str:
            return self._sanitize(str(entry.get(name) or fallback))

        return LegalSourceIndexEntry(
            index_entry_id=value("index_entry_id"),
            source_id=value("source_id"),
            title=value("title"),
            source_type=value("source_type").lower(),
            jurisdiction=value("jurisdiction"),
            effective_date=value("effective_date"),
            citation=value("citation"),
            last_verified_at=value("last_verified_at"),
            freshness_status=value("freshness_status"),
            freshness_expires_at=value("freshness_expires_at"),
            dedupe_key=value("dedupe_key"),
            metadata_hash=value("metadata_hash"),
            index_version=value("index_version", INDEX_VERSION),
            authority_level=value("authority_level"),
            issuer=value("issuer"),
            publication_date=value("publication_date"),
            amendment_date=value("amendment_date"),
            official_url=value("official_url"),
            retrieval_locator=value("retrieval_locator"),
            content_hash=value("content_hash"),
            use_case=value("use_case", "general_legal_reference"),
            ingestion_batch_id=value("ingestion_batch_id"),
            indexed_at=value("indexed_at"),
            retention_bucket=value("retention_bucket"),
            citation_key=value("citation_key"),
            effective_title_key=value("effective_title_key"),
            content_hash_key=value("content_hash_key"),
        )

    def _raw_entry(
        self,
        raw_entries: Iterable[dict[str, Any] | LegalSourceIndexEntry] | None,
        index: int,
        fallback: LegalSourceIndexEntry,
    ) -> dict[str, Any]:
        if raw_entries is None:
            return fallback.to_api()
        raw_list = list(raw_entries)
        if index >= len(raw_list):
            return fallback.to_api()
        item = raw_list[index]
        return item.to_api() if isinstance(item, LegalSourceIndexEntry) else _dict(item)

    def _source_raw_by_id(
        self,
        source_records: Iterable[dict[str, Any] | LegalSourceMetadataRecord] | None,
    ) -> dict[str, dict[str, Any]]:
        if source_records is None:
            return {}
        output: dict[str, dict[str, Any]] = {}
        for item in source_records:
            raw = item.to_api() if isinstance(item, LegalSourceMetadataRecord) else _dict(item)
            source_id = self._sanitize(str(raw.get("id") or ""))
            if source_id:
                output[source_id] = raw
        return output

    def _freshness_snapshot(self, source_type: str, last_verified_at: str, reference_date: date) -> dict[str, str]:
        parsed_verified = self._parse_date(last_verified_at)
        window_days = SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS.get(source_type)
        if not parsed_verified or not window_days:
            return {"status": "unknown", "expires_at": ""}
        expires_at = parsed_verified + timedelta(days=window_days)
        days_since = (reference_date - parsed_verified).days
        warning_after = int(window_days * 0.75)
        if days_since > window_days:
            status = "stale"
        elif days_since > warning_after:
            status = "review_due"
        else:
            status = "fresh"
        return {"status": status, "expires_at": expires_at.isoformat()}

    def _metadata_hash(self, source: LegalSourceMetadataRecord) -> str:
        payload = {
            field: getattr(source, field)
            for field in REQUIRED_SOURCE_RECORD_FIELDS + OPTIONAL_SOURCE_RECORD_FIELDS
        }
        rendered = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(rendered.encode("utf-8")).hexdigest()

    def _expected_dedupe_fields(self, entry: LegalSourceIndexEntry) -> dict[str, str]:
        citation_key = "|".join(
            part
            for part in (
                self._canonical(entry.source_type),
                self._canonical(entry.jurisdiction),
                self._canonical(entry.citation),
            )
            if part
        )
        effective_title_key = "|".join(
            part
            for part in (
                self._canonical(entry.source_type),
                self._canonical(entry.jurisdiction),
                self._canonical(entry.title),
                entry.effective_date,
            )
            if part
        )
        content_hash_key = self._canonical(entry.content_hash)
        return {
            "citation_key": citation_key,
            "effective_title_key": effective_title_key,
            "content_hash_key": content_hash_key,
        }

    def _forbidden_keys(self, raw_value: Any) -> set[str]:
        forbidden = {self._canonical(field) for field in FORBIDDEN_FIELDS}
        found: set[str] = set()

        def walk(value: Any, path: str = "") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    key_text = str(key)
                    canonical = self._canonical(key_text)
                    next_path = f"{path}.{key_text}" if path else key_text
                    if canonical in forbidden:
                        found.add(next_path)
                    walk(child, next_path)
            elif isinstance(value, (list, tuple, set)):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")

        walk(raw_value)
        return found

    def _sensitive_value_findings(self, value: Any, path: str = "$") -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        if isinstance(value, dict):
            for key, child in value.items():
                findings.extend(self._sensitive_value_findings(child, f"{path}.{key}"))
            return findings
        if isinstance(value, (list, tuple, set)):
            for index, child in enumerate(value):
                findings.extend(self._sensitive_value_findings(child, f"{path}[{index}]"))
            return findings
        if isinstance(value, str):
            sanitized = self._sanitize(value)
            if sanitized != value:
                for finding_type, pattern in SENSITIVE_VALUE_PATTERNS:
                    if pattern.search(value):
                        findings.append({"path": path, "type": finding_type})
        return findings

    def _all_values_allowed(self, value: Any, allowed_values: set[str]) -> bool:
        if isinstance(value, (list, tuple, set)):
            return all(str(item) in allowed_values for item in value)
        return str(value) in allowed_values

    def _duplicates(self, values: Iterable[str]) -> set[str]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for value in values:
            if not value:
                continue
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        return duplicates

    def _parse_date(self, value: str) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _sanitize(self, value: str) -> str:
        output = str(value or "")
        for _, pattern in SENSITIVE_VALUE_PATTERNS:
            output = pattern.sub("[redacted]", output)
        return output.strip()

    def _canonical(self, value: str) -> str:
        sanitized = self._sanitize(str(value or "")).lower().strip()
        return NON_KEY_CHARS.sub("-", sanitized).strip("-")


BLOCKING_FLAGS = {
    "missing_required_index_field",
    "forbidden_field_present",
    "sensitive_value_present",
    "duplicate_index_entry_id",
    "duplicate_dedupe_key",
    "unknown_source_type",
    "unsupported_jurisdiction",
    "invalid_effective_date",
    "future_effective_date",
    "invalid_last_verified_at",
    "invalid_freshness_status",
    "freshness_status_mismatch",
    "stale_freshness_metadata",
    "invalid_freshness_expires_at",
    "freshness_expires_at_mismatch",
    "citation_key_mismatch",
    "effective_title_key_mismatch",
    "content_hash_key_mismatch",
    "dedupe_key_mismatch",
}


DEFAULT_SOURCE_RECORDS = (
    LegalSourceMetadataRecord(
        id="cn-civil-code-contract-book",
        title="Synthetic Civil Code contract book metadata",
        source_type="statute",
        jurisdiction="CN-National",
        effective_date="2021-01-01",
        citation="Synthetic citation: Civil Code contract book",
        last_verified_at="2026-05-15",
        authority_level="national_statute",
        issuer="Synthetic national legislature",
        publication_date="2020-05-28",
        official_url="https://example.invalid/cn-civil-code-contract-book",
        retrieval_locator="local-index://civil-code-contract-book",
        content_hash="sha256:synthetic-civil-code-contract-book",
        use_case="contract_review",
        ingestion_batch_id="batch-2026-06-04",
    ),
    LegalSourceMetadataRecord(
        id="cn-labor-contract-law",
        title="Synthetic Labor Contract Law metadata",
        source_type="statute",
        jurisdiction="CN-National",
        effective_date="2013-07-01",
        citation="Synthetic citation: Labor Contract Law",
        last_verified_at="2026-03-01",
        authority_level="national_statute",
        issuer="Synthetic national legislature",
        publication_date="2012-12-28",
        official_url="https://example.invalid/cn-labor-contract-law",
        retrieval_locator="local-index://cn-labor-contract-law",
        content_hash="sha256:synthetic-labor-contract-law",
        use_case="labor_dispute_review",
        ingestion_batch_id="batch-2026-06-04",
    ),
    LegalSourceMetadataRecord(
        id="beijing-rent-template",
        title="Synthetic Beijing residential lease template metadata",
        source_type="template",
        jurisdiction="CN-Beijing",
        effective_date="2025-11-15",
        citation="Synthetic citation: Beijing lease template",
        last_verified_at="2026-02-20",
        authority_level="template",
        issuer="Synthetic template owner",
        publication_date="2025-11-15",
        official_url="https://example.invalid/beijing-rent-template",
        retrieval_locator="local-index://beijing-rent-template",
        content_hash="sha256:synthetic-beijing-rent-template",
        use_case="lease_document_generation",
        ingestion_batch_id="batch-2026-06-04",
    ),
)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
