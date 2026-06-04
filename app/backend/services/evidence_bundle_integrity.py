from __future__ import annotations

from datetime import date
import hashlib
import json
import re
from typing import Any


SENSITIVE_VALUE_PATTERN = re.compile(
    r"("
    r"s" r"k-[A-Za-z0-9]{20,}|"
    r"Bearer\s+[A-Za-z0-9._\-]{16,}|"
    r"api[_-]?key\s*[:=]\s*[^,\s;]+|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\b1[3-9]\d{9}\b|"
    r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b|"
    r"\+\d{1,3}[-.\s]?\d{6,14}\b|"
    r"\b\d{17}[\dXx]\b|"
    r"\b\d{15}\b"
    r")",
    re.IGNORECASE,
)
NON_KEY_CHARS = re.compile(r"[^a-z0-9]+")
LONG_TEXT_LIMIT = 160


class EvidenceBundleIntegrityService:
    """Evaluate metadata-only evidence bundle integrity and duplicate risk."""

    ID_FIELDS = (
        "evidence_id",
        "id",
        "exhibit_id",
        "document_id",
        "file_id",
        "asset_id",
    )
    SOURCE_FIELDS = (
        "source_id",
        "source",
        "source_anchor",
        "source_file_id",
        "source_ref",
        "upload_id",
        "intake_source_id",
        "origin",
    )
    PROOF_PURPOSE_FIELDS = (
        "proof_purpose",
        "purpose",
        "proving_purpose",
        "fact_to_prove",
        "claim_element",
        "issue_to_prove",
    )
    DATE_FIELDS = (
        "evidence_date",
        "date",
        "event_date",
        "occurred_at",
        "document_date",
        "transaction_date",
        "created_at",
    )
    AMOUNT_FIELDS = (
        "amount",
        "amount_cents",
        "amount_yuan",
        "transaction_amount",
        "claimed_amount",
        "contract_amount",
    )
    HASH_FIELDS = (
        "content_hash",
        "hash",
        "checksum",
        "sha256",
        "file_hash",
        "digest",
    )
    FILE_LABEL_FIELDS = (
        "file_name",
        "filename",
        "original_filename",
        "original_file_name",
        "title",
        "label",
        "name",
    )
    FILE_SIZE_FIELDS = ("size", "file_size", "size_bytes", "byte_size")
    RAW_TEXT_FIELDS = {
        "ocr_text",
        "raw_text",
        "full_text",
        "document_body",
        "body",
        "content",
        "extracted_text",
        "transcript",
        "base64",
        "pdf_bytes",
    }

    def build_report(self, payload: list[dict[str, Any]] | dict[str, Any] | None = None) -> dict[str, Any]:
        items = self._items(payload)
        reviews = [self._review_item(item, index) for index, item in enumerate(items, start=1)]
        duplicate_groups = self._duplicate_groups(items, reviews)
        duplicate_group_ids_by_row = self._duplicate_group_ids_by_row(duplicate_groups)
        public_duplicate_groups = self._public_duplicate_groups(duplicate_groups)

        item_reviews = []
        for review in reviews:
            group_ids = duplicate_group_ids_by_row.get(review["row_index"], [])
            status = self._item_status(review, group_ids)
            item_reviews.append(
                {
                    "evidence_id": review["evidence_id"],
                    "safe_hash": review["safe_hash"],
                    "status": status,
                    "missing_fields": review["missing_fields"],
                    "metadata_gaps": review["metadata_gaps"],
                    "duplicate_group_ids": group_ids,
                    "privacy_flags": review["privacy_flags"],
                }
            )

        missing_source_ids = [
            review["evidence_id"] for review in reviews if "source_id" in review["missing_fields"]
        ]
        missing_proof_purpose_ids = [
            review["evidence_id"] for review in reviews if "proof_purpose" in review["missing_fields"]
        ]
        metadata_gap_counts = self._metadata_gap_counts(reviews)
        score = self._score(
            duplicate_groups=public_duplicate_groups,
            missing_source_ids=missing_source_ids,
            missing_proof_purpose_ids=missing_proof_purpose_ids,
            metadata_gap_counts=metadata_gap_counts,
        )
        status = self._status(
            item_count=len(items),
            duplicate_groups=public_duplicate_groups,
            missing_source_ids=missing_source_ids,
            missing_proof_purpose_ids=missing_proof_purpose_ids,
            metadata_gap_counts=metadata_gap_counts,
        )

        return {
            "status": status,
            "score": score,
            "method": {
                "type": "deterministic-evidence-bundle-integrity-v1",
                "notes": [
                    "Evaluates caller-supplied evidence metadata only.",
                    "Does not read files, query databases, call OCR, or call models.",
                    "Raw file names, long OCR text, document bodies, credentials, and PII are not returned.",
                ],
            },
            "summary": {
                "evidence_count": len(items),
                "duplicate_group_count": len(duplicate_groups),
                "missing_source_count": len(missing_source_ids),
                "missing_proof_purpose_count": len(missing_proof_purpose_ids),
                "metadata_gap_total": metadata_gap_counts["total"],
                "ready_for_review": status in {"ready", "review_recommended"},
            },
            "duplicate_groups": public_duplicate_groups,
            "missing_source_ids": missing_source_ids,
            "missing_proof_purpose_ids": missing_proof_purpose_ids,
            "metadata_gap_counts": metadata_gap_counts,
            "item_reviews": item_reviews,
            "recommended_actions": self._recommended_actions(
                item_count=len(items),
                duplicate_groups=public_duplicate_groups,
                missing_source_ids=missing_source_ids,
                missing_proof_purpose_ids=missing_proof_purpose_ids,
                metadata_gap_counts=metadata_gap_counts,
            ),
            "privacy_notes": [
                "Return evidence_id only when it is short and contains no email, phone, ID number, or credential pattern.",
                "Return safe_hash for missing or sensitive identifiers.",
                "Never echo original file names, OCR text, document bodies, full paths, or raw extracted text.",
            ],
            "validation_commands": [
                "python -m pytest tests/test_evidence_bundle_integrity.py -q",
                "python -m compileall services/evidence_bundle_integrity.py",
            ],
        }

    def _items(self, payload: list[dict[str, Any]] | dict[str, Any] | None) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("evidence_items", "items", "evidences", "evidence"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def _review_item(self, item: dict[str, Any], index: int) -> dict[str, Any]:
        raw_id = _first_text(item, self.ID_FIELDS)
        safe_hash = _safe_hash(self._stable_item_fingerprint(item))
        evidence_id = self._safe_evidence_id(raw_id, safe_hash, index)
        source = _first_text(item, self.SOURCE_FIELDS)
        proof_purpose = _first_text(item, self.PROOF_PURPOSE_FIELDS)
        date_value = _first_text(item, self.DATE_FIELDS)
        amount_value = _first_value(item, self.AMOUNT_FIELDS)
        checksum = _first_text(item, self.HASH_FIELDS)
        missing_fields: list[str] = []
        metadata_gaps: list[str] = []

        if not source:
            missing_fields.append("source_id")
        if not proof_purpose:
            missing_fields.append("proof_purpose")

        if not date_value:
            metadata_gaps.append("missing_date")
        elif not _valid_iso_date(date_value):
            metadata_gaps.append("invalid_date")

        if not _present(amount_value):
            metadata_gaps.append("missing_amount")
        elif not _valid_amount(amount_value):
            metadata_gaps.append("invalid_amount")

        if not checksum:
            metadata_gaps.append("missing_checksum")

        raw_text_count = self._raw_text_field_count(item)
        sensitive_value_count = self._sensitive_value_count(item)
        privacy_flags: list[str] = []
        if raw_text_count:
            privacy_flags.append("raw_text_field_present")
        if sensitive_value_count:
            privacy_flags.append("sensitive_value_detected")

        return {
            "row_index": index,
            "evidence_id": evidence_id,
            "safe_hash": safe_hash,
            "missing_fields": missing_fields,
            "metadata_gaps": metadata_gaps,
            "privacy_flags": privacy_flags,
            "raw_text_field_count": raw_text_count,
            "sensitive_value_count": sensitive_value_count,
        }

    def _safe_evidence_id(self, raw_id: str, safe_hash: str, index: int) -> str:
        if not raw_id:
            return f"item-{index:03d}-{safe_hash}"
        if _safe_short_label(raw_id):
            return raw_id
        return f"hash:{safe_hash}"

    def _stable_item_fingerprint(self, item: dict[str, Any]) -> str:
        return json.dumps(_bounded_for_hash(item), ensure_ascii=False, sort_keys=True, default=str)

    def _duplicate_groups(self, items: list[dict[str, Any]], reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
        indexes: dict[tuple[str, str], list[int]] = {}
        for item, review in zip(items, reviews, strict=False):
            for key_type, key_value in self._dedupe_keys(item, review):
                indexes.setdefault((key_type, key_value), []).append(review["row_index"])

        review_by_row = {review["row_index"]: review for review in reviews}
        groups: list[dict[str, Any]] = []
        seen_row_sets: set[tuple[int, ...]] = set()
        key_priority = {"content_hash": 0, "evidence_id": 1, "metadata_fingerprint": 2, "file_fingerprint": 3}

        for (key_type, key_value), row_indexes in sorted(
            indexes.items(), key=lambda item: (key_priority.get(item[0][0], 99), item[0][0], item[0][1])
        ):
            if len(row_indexes) < 2:
                continue
            row_set = tuple(sorted(row_indexes))
            if row_set in seen_row_sets:
                continue
            seen_row_sets.add(row_set)
            group_id = f"duplicate-{len(groups) + 1:03d}"
            members = [
                {
                    "row_index": row_index,
                    "evidence_id": review_by_row[row_index]["evidence_id"],
                    "safe_hash": review_by_row[row_index]["safe_hash"],
                }
                for row_index in row_set
            ]
            groups.append(
                {
                    "group_id": group_id,
                    "match_on": key_type,
                    "group_hash": _safe_hash(key_value),
                    "count": len(row_set),
                    "evidence_ids": [member["evidence_id"] for member in members],
                    "members": members,
                    "recommended_action": "Keep one canonical evidence record and mark the others as duplicates before review.",
                }
            )
        return groups

    def _dedupe_keys(self, item: dict[str, Any], review: dict[str, Any]) -> list[tuple[str, str]]:
        keys: list[tuple[str, str]] = []
        raw_id = _first_text(item, self.ID_FIELDS)
        checksum = _first_text(item, self.HASH_FIELDS)
        file_label = _first_text(item, self.FILE_LABEL_FIELDS)
        file_size = _first_text(item, self.FILE_SIZE_FIELDS)
        source = _first_text(item, self.SOURCE_FIELDS)
        date_value = _first_text(item, self.DATE_FIELDS)
        amount_value = _first_value(item, self.AMOUNT_FIELDS)

        if checksum:
            keys.append(("content_hash", _canonical(checksum)))
        if raw_id:
            keys.append(("evidence_id", _canonical(raw_id)))

        file_parts = [_canonical(file_label), _canonical(file_size)]
        if any(file_parts):
            keys.append(("file_fingerprint", "|".join(file_parts)))

        metadata_parts = [
            _canonical(file_label),
            _canonical(source),
            _canonical(date_value),
            _canonical(str(amount_value) if amount_value is not None else ""),
        ]
        if sum(1 for part in metadata_parts if part) >= 2:
            keys.append(("metadata_fingerprint", "|".join(metadata_parts)))

        if not keys:
            keys.append(("metadata_fingerprint", review["safe_hash"]))
        return [(key_type, key_value) for key_type, key_value in keys if key_value.strip("|")]

    def _duplicate_group_ids_by_row(self, duplicate_groups: list[dict[str, Any]]) -> dict[int, list[str]]:
        result: dict[int, list[str]] = {}
        for group in duplicate_groups:
            for member in group["members"]:
                row_index = member["row_index"]
                result.setdefault(row_index, []).append(group["group_id"])
        return result

    def _public_duplicate_groups(self, duplicate_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
        public_groups: list[dict[str, Any]] = []
        for group in duplicate_groups:
            members = [
                {
                    "evidence_id": member["evidence_id"],
                    "safe_hash": member["safe_hash"],
                }
                for member in group["members"]
            ]
            public_groups.append(
                {
                    "group_id": group["group_id"],
                    "match_on": group["match_on"],
                    "group_hash": group["group_hash"],
                    "count": group["count"],
                    "evidence_ids": group["evidence_ids"],
                    "members": members,
                    "recommended_action": group["recommended_action"],
                }
            )
        return public_groups

    def _item_status(self, review: dict[str, Any], duplicate_group_ids: list[str]) -> str:
        if review["missing_fields"] or duplicate_group_ids:
            return "fail"
        if review["metadata_gaps"] or review["privacy_flags"]:
            return "warn"
        return "pass"

    def _metadata_gap_counts(self, reviews: list[dict[str, Any]]) -> dict[str, int]:
        counts = {
            "missing_date": 0,
            "invalid_date": 0,
            "missing_amount": 0,
            "invalid_amount": 0,
            "missing_checksum": 0,
            "raw_text_field_present": 0,
            "sensitive_value_detected": 0,
        }
        for review in reviews:
            for gap in review["metadata_gaps"]:
                counts[gap] += 1
            if "raw_text_field_present" in review["privacy_flags"]:
                counts["raw_text_field_present"] += 1
            if "sensitive_value_detected" in review["privacy_flags"]:
                counts["sensitive_value_detected"] += 1
        counts["total"] = sum(counts.values())
        return counts

    def _score(
        self,
        *,
        duplicate_groups: list[dict[str, Any]],
        missing_source_ids: list[str],
        missing_proof_purpose_ids: list[str],
        metadata_gap_counts: dict[str, int],
    ) -> int:
        penalty = 0
        penalty += len(duplicate_groups) * 20
        penalty += sum(group["count"] for group in duplicate_groups) * 4
        penalty += len(missing_source_ids) * 15
        penalty += len(missing_proof_purpose_ids) * 15
        penalty += metadata_gap_counts["missing_date"] * 5
        penalty += metadata_gap_counts["invalid_date"] * 8
        penalty += metadata_gap_counts["missing_amount"] * 3
        penalty += metadata_gap_counts["invalid_amount"] * 5
        penalty += metadata_gap_counts["missing_checksum"] * 2
        penalty += metadata_gap_counts["raw_text_field_present"] * 5
        penalty += metadata_gap_counts["sensitive_value_detected"] * 5
        return max(0, 100 - penalty)

    def _status(
        self,
        *,
        item_count: int,
        duplicate_groups: list[dict[str, Any]],
        missing_source_ids: list[str],
        missing_proof_purpose_ids: list[str],
        metadata_gap_counts: dict[str, int],
    ) -> str:
        if item_count == 0:
            return "template"
        if duplicate_groups or missing_source_ids or missing_proof_purpose_ids:
            return "blocked"
        if metadata_gap_counts["total"]:
            return "review_recommended"
        return "ready"

    def _recommended_actions(
        self,
        *,
        item_count: int,
        duplicate_groups: list[dict[str, Any]],
        missing_source_ids: list[str],
        missing_proof_purpose_ids: list[str],
        metadata_gap_counts: dict[str, int],
    ) -> list[str]:
        if item_count == 0:
            return [
                "Submit evidence metadata rows with evidence_id, source_id, proof_purpose, date, amount, and checksum.",
            ]

        actions: list[str] = []
        if duplicate_groups:
            actions.append("Quarantine duplicate groups, pick one canonical evidence record, and link duplicate records to it.")
        if missing_source_ids:
            actions.append("Populate source_id or source_anchor for every evidence row before bundle review.")
        if missing_proof_purpose_ids:
            actions.append("Add proof_purpose values that map each evidence row to a fact, issue, or claim element.")
        if metadata_gap_counts["missing_date"] or metadata_gap_counts["invalid_date"]:
            actions.append("Normalize evidence dates to ISO format YYYY-MM-DD.")
        if metadata_gap_counts["missing_amount"] or metadata_gap_counts["invalid_amount"]:
            actions.append("Populate numeric amount metadata, using 0 only when the amount is intentionally not applicable.")
        if metadata_gap_counts["missing_checksum"]:
            actions.append("Attach a local checksum or content_hash to improve exact duplicate detection.")
        if metadata_gap_counts["raw_text_field_present"] or metadata_gap_counts["sensitive_value_detected"]:
            actions.append("Strip raw OCR/body fields and sensitive values before persisting bundle integrity results.")
        if not actions:
            actions.append("Evidence bundle metadata is ready for downstream legal review.")
        return actions

    def _raw_text_field_count(self, item: dict[str, Any]) -> int:
        count = 0

        def walk(value: Any) -> None:
            nonlocal count
            if isinstance(value, dict):
                for key, child in value.items():
                    if _canonical(str(key)).replace("-", "_") in self.RAW_TEXT_FIELDS:
                        count += 1
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(item)
        return count

    def _sensitive_value_count(self, item: dict[str, Any]) -> int:
        count = 0

        def walk(value: Any) -> None:
            nonlocal count
            if isinstance(value, dict):
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
            elif isinstance(value, str):
                if SENSITIVE_VALUE_PATTERN.search(value):
                    count += 1

        walk(item)
        return count


def _first_text(item: dict[str, Any], fields: tuple[str, ...]) -> str:
    value = _first_value(item, fields)
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _first_value(item: dict[str, Any], fields: tuple[str, ...]) -> Any:
    for field in fields:
        value = item.get(field)
        if _present(value):
            return value
    metadata = item.get("metadata")
    if isinstance(metadata, dict):
        for field in fields:
            value = metadata.get(field)
            if _present(value):
                return value
    return None


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _safe_short_label(value: str) -> bool:
    text = value.strip()
    if not text or len(text) > 80:
        return False
    if SENSITIVE_VALUE_PATTERN.search(text):
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9._:/#-]+", text))


def _valid_iso_date(value: str) -> bool:
    text = value.strip()
    candidate = text[:10] if len(text) >= 10 else text
    try:
        date.fromisoformat(candidate)
    except ValueError:
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate))


def _valid_amount(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    text = text.replace(",", "")
    text = re.sub(r"^(rmb|cny|usd|eur|gbp|jpy|\$)\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(yuan|rmb|cny|usd|dollars?)$", "", text, flags=re.IGNORECASE)
    try:
        float(text)
    except ValueError:
        return False
    return True


def _canonical(value: str) -> str:
    safe = SENSITIVE_VALUE_PATTERN.sub("[redacted]", str(value or "")).lower().strip()
    return NON_KEY_CHARS.sub("-", safe).strip("-")


def _safe_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _bounded_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _bounded_for_hash(child) for key, child in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_bounded_for_hash(child) for child in value[:50]]
    if isinstance(value, str):
        return value[:LONG_TEXT_LIMIT]
    return value
