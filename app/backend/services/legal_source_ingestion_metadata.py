from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
import re
from typing import Any


REFERENCE_DATE = date(2026, 6, 4)
SCHEMA_VERSION = "legal-source-ingestion-metadata-v1"

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

REQUIRED_FIELDS = (
    "id",
    "title",
    "source_type",
    "jurisdiction",
    "effective_date",
    "citation",
    "last_verified_at",
)

OPTIONAL_METADATA_FIELDS = (
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

FORBIDDEN_FIELDS = (
    "raw_text",
    "full_text",
    "document_body",
    "html",
    "pdf_bytes",
    "base64_pdf",
    "ocr_text",
    "client_name",
    "client_email",
    "phone",
    "personal_id",
    "case_number",
    "matter_id",
    "prompt",
    "model_response",
    "authorization",
    "api_key",
    "password",
)

SENSITIVE_VALUE_PATTERN = re.compile(
    r"(s" r"k-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._\-]{16,}|APP_AI_KEY\s*=\s*[^,\s;]+|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password)",
    re.IGNORECASE,
)
NON_KEY_CHARS = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class LegalSourceIngestionRecord:
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


class LegalSourceIngestionMetadataService:
    """Define and evaluate local-only legal source ingestion metadata."""

    def build_metadata_contract(
        self,
        records: list[dict[str, Any]] | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> dict[str, Any]:
        source_records = self._record_items(records)
        evaluation = self.evaluate_records(records if records is not None else source_records, reference_date)
        return {
            "schema_version": SCHEMA_VERSION,
            "status": evaluation["status"],
            "record_schema": self._record_schema(),
            "jurisdiction_fields": self._jurisdiction_fields(),
            "effective_date_fields": self._effective_date_fields(),
            "citation_fields": self._citation_fields(),
            "freshness_fields": self._freshness_fields(),
            "dedupe_keys": self._dedupe_key_definitions(),
            "forbidden_fields": self._forbidden_field_definitions(),
            "sample_source_records": [record.to_api() for record in source_records],
            "sample_evaluation": evaluation,
            "privacy_note": (
                "This service accepts metadata only. It must not receive raw legal text, client facts, prompts, model "
                "responses, account credentials, API keys, or private matter identifiers."
            ),
            "integration_note": (
                "This contract is intentionally adjacent to legal_source_freshness_policy. Routers, release gates, and "
                "ledgers can integrate it later without requiring network, model, database, or filesystem state."
            ),
            "validation_commands": [
                "python -m pytest tests/test_legal_source_ingestion_metadata.py -q",
                "python -m compileall services/legal_source_ingestion_metadata.py",
            ],
        }

    def evaluate_records(
        self,
        records: list[LegalSourceIngestionRecord] | list[dict[str, Any]] | None = None,
        reference_date: date = REFERENCE_DATE,
    ) -> dict[str, Any]:
        record_items = self._record_items(records)
        duplicate_ids = self._duplicate_ids(record_items)
        dedupe_index = self._dedupe_index(record_items)
        reviews = [
            self._review_record(
                record=record,
                raw_record=self._raw_record(record, records, index),
                duplicate_ids=duplicate_ids,
                duplicate_dedupe_keys=dedupe_index,
                reference_date=reference_date,
            )
            for index, record in enumerate(record_items)
        ]
        blocking = [review for review in reviews if review["status"] == "fail"]
        warnings = [review for review in reviews if review["status"] == "warn"]
        return {
            "status": "blocked" if blocking else ("review_recommended" if warnings else "ready"),
            "summary": {
                "record_count": len(reviews),
                "ready_count": sum(1 for review in reviews if review["status"] == "pass"),
                "warning_count": len(warnings),
                "blocked_count": len(blocking),
                "duplicate_record_ids": sorted(duplicate_ids),
                "duplicate_dedupe_keys": sorted(
                    key for key, ids in dedupe_index.items() if len(ids) > 1 and key != ""
                ),
                "forbidden_field_record_ids": [
                    review["id"] for review in reviews if "forbidden_field_present" in review["flags"]
                ],
                "missing_required_record_ids": [
                    review["id"] for review in reviews if "missing_required_field" in review["flags"]
                ],
                "reference_date": reference_date.isoformat(),
            },
            "record_reviews": reviews,
            "recommended_actions": self._recommended_actions(blocking, warnings),
        }

    def _record_items(
        self,
        records: list[LegalSourceIngestionRecord] | list[dict[str, Any]] | None,
    ) -> list[LegalSourceIngestionRecord]:
        if records is None:
            return list(DEFAULT_SAMPLE_RECORDS)
        items: list[LegalSourceIngestionRecord] = []
        for index, record in enumerate(records, start=1):
            if isinstance(record, LegalSourceIngestionRecord):
                items.append(record)
            else:
                items.append(self._coerce_record(index, record if isinstance(record, dict) else {}))
        return items

    def _coerce_record(self, index: int, record: dict[str, Any]) -> LegalSourceIngestionRecord:
        def value(name: str, fallback: str = "") -> str:
            return self._sanitize(str(record.get(name) or fallback))

        return LegalSourceIngestionRecord(
            id=value("id", f"source-{index}"),
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

    def _raw_record(
        self,
        record: LegalSourceIngestionRecord,
        original: list[LegalSourceIngestionRecord] | list[dict[str, Any]] | None,
        index: int,
    ) -> dict[str, Any]:
        if original is None:
            return record.to_api()
        if index >= len(original):
            return record.to_api()
        item = original[index]
        return item.to_api() if isinstance(item, LegalSourceIngestionRecord) else _dict(item)

    def _review_record(
        self,
        *,
        record: LegalSourceIngestionRecord,
        raw_record: dict[str, Any],
        duplicate_ids: set[str],
        duplicate_dedupe_keys: dict[str, set[str]],
        reference_date: date,
    ) -> dict[str, Any]:
        flags: list[str] = []
        actions: list[str] = []
        missing_required = [field for field in REQUIRED_FIELDS if not getattr(record, field)]
        forbidden_present = self._forbidden_keys(raw_record)
        parsed_effective = self._parse_date(record.effective_date)
        parsed_verified = self._parse_date(record.last_verified_at)
        parsed_publication = self._parse_date(record.publication_date)
        parsed_amendment = self._parse_date(record.amendment_date)
        dedupe_keys = self._record_dedupe_keys(record)

        if missing_required:
            flags.append("missing_required_field")
            actions.append("Populate all required identity, jurisdiction, citation, and freshness metadata fields.")

        if forbidden_present:
            flags.append("forbidden_field_present")
            actions.append("Remove forbidden raw content, private matter, credential, prompt, or model-output fields.")

        if record.id in duplicate_ids:
            flags.append("duplicate_record_id")
            actions.append("Use a stable unique source id before ingestion.")

        duplicate_key_names = [
            key_name for key_name, key_value in dedupe_keys.items() if key_value and len(duplicate_dedupe_keys[key_value]) > 1
        ]
        if duplicate_key_names:
            flags.append("duplicate_dedupe_key")
            actions.append("Quarantine duplicate source metadata and keep one canonical source record.")

        if record.source_type and record.source_type not in SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS:
            flags.append("unknown_source_type")
            actions.append("Map the source type to a known freshness window before ingestion.")

        if record.jurisdiction and record.jurisdiction not in SUPPORTED_JURISDICTIONS:
            flags.append("unsupported_jurisdiction")
            actions.append("Route unsupported jurisdiction metadata to manual legal knowledge review.")

        if record.effective_date and parsed_effective is None:
            flags.append("invalid_effective_date")
            actions.append("Use ISO date format YYYY-MM-DD for effective_date.")
        elif parsed_effective and parsed_effective > reference_date:
            flags.append("future_effective_date")
            actions.append("Do not ingest this source as active before its effective date.")

        for field_name, parsed_value in (
            ("publication_date", parsed_publication),
            ("amendment_date", parsed_amendment),
        ):
            raw_value = getattr(record, field_name)
            if raw_value and parsed_value is None:
                flags.append(f"invalid_{field_name}")
                actions.append(f"Use ISO date format YYYY-MM-DD for {field_name}.")

        if record.last_verified_at and parsed_verified is None:
            flags.append("invalid_last_verified_at")
            actions.append("Use ISO date format YYYY-MM-DD for last_verified_at.")

        freshness = self._freshness_snapshot(record, parsed_verified, reference_date)
        if freshness["status"] == "stale":
            flags.append("stale_freshness_metadata")
            actions.append("Refresh the source metadata before adding it to the retrievable corpus.")
        elif freshness["status"] == "review_due":
            flags.append("freshness_review_due")
            actions.append("Schedule legal source freshness review before release expansion.")

        if record.citation and len(record.citation) < 8:
            flags.append("weak_citation")
            actions.append("Use a stable citation that a reviewer can trace to the source.")

        if any(flag in flags for flag in BLOCKING_FLAGS):
            status = "fail"
        elif flags:
            status = "warn"
        else:
            status = "pass"

        return {
            "id": record.id,
            "title": record.title,
            "source_type": record.source_type,
            "jurisdiction": record.jurisdiction,
            "effective_date": record.effective_date,
            "citation": record.citation,
            "last_verified_at": record.last_verified_at,
            "freshness": freshness,
            "dedupe_keys": dedupe_keys,
            "duplicate_key_names": duplicate_key_names,
            "forbidden_fields_present": sorted(forbidden_present),
            "missing_required_fields": missing_required,
            "status": status,
            "flags": flags,
            "recommended_actions": actions or ["Source metadata is ready for local ingestion evaluation."],
        }

    def _freshness_snapshot(
        self,
        record: LegalSourceIngestionRecord,
        parsed_verified: date | None,
        reference_date: date,
    ) -> dict[str, Any]:
        window_days = SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS.get(record.source_type)
        if not parsed_verified or not window_days:
            return {
                "status": "unknown",
                "window_days": window_days,
                "days_since_last_verified": None,
                "next_review_due_at": "",
                "policy_ref": "legal_source_freshness_policy",
            }
        days_since = (reference_date - parsed_verified).days
        next_review_due = parsed_verified + timedelta(days=window_days)
        warning_after = int(window_days * 0.75)
        if days_since > window_days:
            status = "stale"
        elif days_since > warning_after:
            status = "review_due"
        else:
            status = "fresh"
        return {
            "status": status,
            "window_days": window_days,
            "warning_after_days": warning_after,
            "days_since_last_verified": days_since,
            "next_review_due_at": next_review_due.isoformat(),
            "policy_ref": "legal_source_freshness_policy",
        }

    def _duplicate_ids(self, records: list[LegalSourceIngestionRecord]) -> set[str]:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for record in records:
            if not record.id:
                continue
            if record.id in seen:
                duplicates.add(record.id)
            seen.add(record.id)
        return duplicates

    def _dedupe_index(self, records: list[LegalSourceIngestionRecord]) -> dict[str, set[str]]:
        index: dict[str, set[str]] = {}
        for record in records:
            for key in self._record_dedupe_keys(record).values():
                if not key:
                    continue
                index.setdefault(key, set()).add(record.id)
        return index

    def _record_dedupe_keys(self, record: LegalSourceIngestionRecord) -> dict[str, str]:
        citation = self._canonical(record.citation)
        title = self._canonical(record.title)
        issuer = self._canonical(record.issuer)
        content_hash = self._canonical(record.content_hash)
        source_type = self._canonical(record.source_type)
        jurisdiction = self._canonical(record.jurisdiction)
        return {
            "citation_key": "|".join(part for part in (source_type, jurisdiction, citation) if part),
            "effective_title_key": "|".join(
                part for part in (source_type, jurisdiction, title, record.effective_date) if part
            ),
            "issuer_title_key": "|".join(part for part in (source_type, jurisdiction, issuer, title) if part),
            "content_hash_key": content_hash,
        }

    def _record_schema(self) -> dict[str, Any]:
        fields = []
        for name in REQUIRED_FIELDS:
            fields.append(self._field_definition(name, required=True))
        for name in OPTIONAL_METADATA_FIELDS:
            fields.append(self._field_definition(name, required=False))
        return {
            "type": "object",
            "required_fields": list(REQUIRED_FIELDS),
            "optional_metadata_fields": list(OPTIONAL_METADATA_FIELDS),
            "allowed_fields": list(REQUIRED_FIELDS + OPTIONAL_METADATA_FIELDS),
            "fields": fields,
        }

    def _field_definition(self, name: str, required: bool) -> dict[str, Any]:
        descriptions = {
            "id": "Stable local source identifier.",
            "title": "Human-readable title for reviewer display.",
            "source_type": "One of statute, regulation, judicial_interpretation, case, template, or internal_note.",
            "jurisdiction": "Jurisdiction tag used for retrieval filtering and mismatch checks.",
            "effective_date": "Date the source became legally effective, in YYYY-MM-DD format.",
            "citation": "Stable citation text that can be checked by a legal reviewer.",
            "last_verified_at": "Date the source metadata was last verified locally, in YYYY-MM-DD format.",
            "authority_level": "Optional authority rank such as national_statute or local_regulation.",
            "issuer": "Optional public issuer name.",
            "publication_date": "Optional publication date in YYYY-MM-DD format.",
            "amendment_date": "Optional latest amendment date in YYYY-MM-DD format.",
            "official_url": "Optional public source URL or official locator.",
            "retrieval_locator": "Optional local retrieval pointer that contains no raw source text.",
            "content_hash": "Optional hash for dedupe; never store the raw source body here.",
            "use_case": "Optional local use case label.",
            "ingestion_batch_id": "Optional local batch identifier.",
        }
        examples = {
            "id": "cn-civil-code-contract-book",
            "title": "Synthetic Civil Code contract book metadata",
            "source_type": "statute",
            "jurisdiction": "CN-National",
            "effective_date": "2021-01-01",
            "citation": "Synthetic citation: Civil Code contract book",
            "last_verified_at": "2026-05-15",
            "authority_level": "national_statute",
            "issuer": "Synthetic national legislature",
            "publication_date": "2020-05-28",
            "amendment_date": "",
            "official_url": "https://example.invalid/legal-source",
            "retrieval_locator": "local-index://civil-code-contract-book",
            "content_hash": "sha256:synthetic",
            "use_case": "contract_review",
            "ingestion_batch_id": "batch-2026-06-04",
        }
        return {
            "name": name,
            "type": "string",
            "required": required,
            "description": descriptions[name],
            "example": examples[name],
        }

    def _jurisdiction_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "jurisdiction",
                "required": True,
                "allowed_values": sorted(SUPPORTED_JURISDICTIONS),
                "purpose": "Filters retrieval and prevents cross-jurisdiction citation drift.",
            }
        ]

    def _effective_date_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "effective_date",
                "required": True,
                "format": "YYYY-MM-DD",
                "purpose": "Prevents citing sources that are not yet effective or cannot be time-bounded.",
            },
            {
                "name": "publication_date",
                "required": False,
                "format": "YYYY-MM-DD",
                "purpose": "Helps reviewers distinguish publication from legal effectiveness.",
            },
            {
                "name": "amendment_date",
                "required": False,
                "format": "YYYY-MM-DD",
                "purpose": "Captures latest known amendment metadata without storing raw law text.",
            },
        ]

    def _citation_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "citation",
                "required": True,
                "purpose": "Stable citation text for reviewer traceability.",
            },
            {
                "name": "official_url",
                "required": False,
                "purpose": "Public locator for manual review; not fetched by this service.",
            },
            {
                "name": "retrieval_locator",
                "required": False,
                "purpose": "Local retrieval pointer that must not contain raw legal or client text.",
            },
        ]

    def _freshness_fields(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "last_verified_at",
                "required": True,
                "format": "YYYY-MM-DD",
                "purpose": "Anchors freshness checks before the source enters retrieval.",
            },
            {
                "name": "source_type",
                "required": True,
                "windows_days": dict(sorted(SOURCE_TYPE_FRESHNESS_WINDOWS_DAYS.items())),
                "purpose": "Selects the local freshness window used by the adjacent freshness policy.",
            },
            {
                "name": "content_hash",
                "required": False,
                "purpose": "Optional dedupe fingerprint; raw source text remains forbidden.",
            },
        ]

    def _dedupe_key_definitions(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "citation_key",
                "fields": ["source_type", "jurisdiction", "citation"],
                "purpose": "Primary key for canonical citation duplicates.",
            },
            {
                "name": "effective_title_key",
                "fields": ["source_type", "jurisdiction", "title", "effective_date"],
                "purpose": "Finds repeated source records when citation formatting differs.",
            },
            {
                "name": "issuer_title_key",
                "fields": ["source_type", "jurisdiction", "issuer", "title"],
                "purpose": "Finds repeated issuer-title records across batches.",
            },
            {
                "name": "content_hash_key",
                "fields": ["content_hash"],
                "purpose": "Optional exact-fingerprint dedupe when the ingest pipeline has already hashed content.",
            },
        ]

    def _forbidden_field_definitions(self) -> list[dict[str, str]]:
        return [
            {
                "name": field,
                "reason": "Ingestion metadata must not store raw source text, private matter data, prompts, model output, or credentials.",
            }
            for field in FORBIDDEN_FIELDS
        ]

    def _forbidden_keys(self, raw_record: dict[str, Any]) -> set[str]:
        forbidden = {self._canonical(field) for field in FORBIDDEN_FIELDS}
        found: set[str] = set()

        def walk(value: Any, path: str = "") -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    canonical = self._canonical(str(key))
                    if canonical in forbidden:
                        found.add(path + str(key) if path else str(key))
                    walk(child, f"{path}{key}.")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}{index}.")

        walk(raw_record)
        return found

    def _recommended_actions(
        self,
        blocking: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> list[str]:
        if blocking:
            return [
                "Block ingestion for failing source records and quarantine duplicate or forbidden-field records.",
                "Populate jurisdiction, effective_date, citation, and last_verified_at before routing to freshness review.",
            ]
        if warnings:
            return [
                "Review weak citations, duplicate candidates, and review-due freshness metadata before retrieval expansion.",
                "Keep warning records out of automatic legal answer generation until a legal knowledge owner approves them.",
            ]
        return [
            "Use these records as metadata-only candidates for local retrieval ingestion.",
            "Run the adjacent legal source freshness policy before enabling citation in generated output.",
        ]

    def _parse_date(self, value: str) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _sanitize(self, value: str) -> str:
        return SENSITIVE_VALUE_PATTERN.sub("[redacted]", value).strip()

    def _canonical(self, value: str) -> str:
        value = SENSITIVE_VALUE_PATTERN.sub("[redacted]", str(value or "")).lower().strip()
        return NON_KEY_CHARS.sub("-", value).strip("-")


BLOCKING_FLAGS = {
    "missing_required_field",
    "forbidden_field_present",
    "duplicate_record_id",
    "duplicate_dedupe_key",
    "unknown_source_type",
    "unsupported_jurisdiction",
    "invalid_effective_date",
    "future_effective_date",
    "invalid_last_verified_at",
    "stale_freshness_metadata",
}


DEFAULT_SAMPLE_RECORDS = (
    LegalSourceIngestionRecord(
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
    LegalSourceIngestionRecord(
        id="sh-local-labor-guidance",
        title="Synthetic Shanghai labor guidance metadata",
        source_type="regulation",
        jurisdiction="CN-Shanghai",
        effective_date="2025-01-01",
        citation="Synthetic citation: Shanghai labor guidance",
        last_verified_at="2025-07-10",
        authority_level="local_regulation",
        issuer="Synthetic Shanghai authority",
        publication_date="2024-12-15",
        official_url="https://example.invalid/sh-local-labor-guidance",
        retrieval_locator="local-index://sh-local-labor-guidance",
        content_hash="sha256:synthetic-sh-labor-guidance",
        use_case="labor_dispute_review",
        ingestion_batch_id="batch-2026-06-04",
    ),
    LegalSourceIngestionRecord(
        id="cn-lease-template-missing-citation",
        title="Synthetic lease template metadata needing citation",
        source_type="template",
        jurisdiction="CN-Beijing",
        effective_date="2025-11-15",
        citation="",
        last_verified_at="2026-02-20",
        authority_level="template",
        issuer="Synthetic template owner",
        publication_date="2025-11-15",
        official_url="https://example.invalid/cn-lease-template",
        retrieval_locator="local-index://cn-lease-template",
        content_hash="sha256:synthetic-cn-lease-template",
        use_case="lease_document_generation",
        ingestion_batch_id="batch-2026-06-04",
    ),
)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
