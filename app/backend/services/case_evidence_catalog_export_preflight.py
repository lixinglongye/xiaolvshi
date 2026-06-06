from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from services.evidence_bundle_integrity import EvidenceBundleIntegrityService, SENSITIVE_VALUE_PATTERN
from services.evidence_exhibit_package_policy import EvidenceExhibitPackagePolicyService


SAFE_REF_PATTERN = re.compile(r"^[A-Za-z0-9._:/#-]{1,80}$")


class CaseEvidenceCatalogExportPreflightService:
    """Join exhibit package and bundle integrity checks for evidence catalog drafts."""

    PREFLIGHT_ID = "case-evidence-catalog-export-preflight-v1"

    def __init__(
        self,
        *,
        package_policy_service: EvidenceExhibitPackagePolicyService | None = None,
        bundle_integrity_service: EvidenceBundleIntegrityService | None = None,
    ) -> None:
        self.package_policy_service = package_policy_service or EvidenceExhibitPackagePolicyService()
        self.bundle_integrity_service = bundle_integrity_service or EvidenceBundleIntegrityService()

    def build_preflight(self, rows: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
        row_list = [dict(row) for row in rows or [] if isinstance(row, Mapping)]
        package_policy = self.package_policy_service.build_policy(
            {"exhibits": [self._package_exhibit(row, index) for index, row in enumerate(row_list, start=1)]}
        )
        bundle_integrity = self.bundle_integrity_service.build_report(
            {"items": [self._integrity_item(row, index) for index, row in enumerate(row_list, start=1)]}
        )
        status = self._status(row_list, package_policy, bundle_integrity)

        return {
            "preflight_id": self.PREFLIGHT_ID,
            "status": status,
            "export_allowed": status == "ready_for_export",
            "draft_generation_allowed": True,
            "summary": {
                "evidence_row_count": len(row_list),
                "package_policy_status": package_policy["status"],
                "bundle_integrity_status": bundle_integrity["status"],
                "blocking_issue_count": len(package_policy["blocking_issues"]),
                "blocked_package_check_count": sum(
                    1 for check in package_policy["package_checks"] if check["status"] == "blocked"
                ),
                "integrity_score": bundle_integrity["score"],
                "duplicate_group_count": bundle_integrity["summary"]["duplicate_group_count"],
                "missing_source_count": bundle_integrity["summary"]["missing_source_count"],
                "missing_proof_purpose_count": bundle_integrity["summary"]["missing_proof_purpose_count"],
                "metadata_gap_total": bundle_integrity["summary"]["metadata_gap_total"],
                "raw_text_returned": False,
                "evidence_names_returned": False,
                "source_values_returned": False,
                "files_read": False,
                "model_called": False,
            },
            "package_policy": {
                "status": package_policy["status"],
                "policy_id": package_policy["policy_id"],
                "summary": package_policy["summary"],
                "package_checks": package_policy["package_checks"],
                "blocking_issues": package_policy["blocking_issues"],
                "review_actions": package_policy["review_actions"],
                "export_manifest_fields": package_policy["export_manifest_fields"],
            },
            "bundle_integrity": {
                "status": bundle_integrity["status"],
                "score": bundle_integrity["score"],
                "summary": bundle_integrity["summary"],
                "duplicate_groups": bundle_integrity["duplicate_groups"],
                "missing_source_ids": bundle_integrity["missing_source_ids"],
                "missing_proof_purpose_ids": bundle_integrity["missing_proof_purpose_ids"],
                "metadata_gap_counts": bundle_integrity["metadata_gap_counts"],
                "item_reviews": bundle_integrity["item_reviews"],
                "recommended_actions": bundle_integrity["recommended_actions"],
            },
            "review_actions": self._review_actions(package_policy, bundle_integrity),
            "privacy_boundary": {
                "input_rows_sanitized": True,
                "raw_evidence_rows_returned": False,
                "raw_document_text_returned": False,
                "evidence_names_returned": False,
                "source_values_returned": False,
                "file_names_returned": False,
                "pii_returned": False,
                "credentials_returned": False,
                "files_read": False,
                "model_called": False,
            },
            "claim_boundary": {
                "draft_catalog_created": True,
                "ready_for_external_delivery": status == "ready_for_export",
                "lawyer_review_completed": False,
                "court_filing_completed": False,
                "attachment_bundle_created": False,
                "checksums_verified_against_files": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_case_evidence_catalog_export_preflight.py tests/test_case_generation_quota.py -q",
                "python -m py_compile services/case_evidence_catalog_export_preflight.py services/case_intelligence.py",
            ],
        }

    def _package_exhibit(self, row: Mapping[str, Any], index: int) -> dict[str, Any]:
        exhibit_ref = self._safe_ref(
            self._first_text(row, "exhibit_number", "evidence_no", "evidence_id", "id"),
            index=index,
            prefix="E",
        )
        attachment_ref = self._safe_ref(
            self._first_text(row, "attachment_number", "attachment_no", "attachment_id"),
            index=index,
            prefix="A",
            allow_empty=True,
        )
        return {
            "exhibit_number": exhibit_ref,
            "attachment_number": attachment_ref,
            "title": self._redacted_label(index),
            "source_anchor": self._first_text(row, "source_anchor", "source_id", "evidence_source", "source"),
            "page_anchor": self._first_text(row, "page_anchor", "page_range", "page_refs"),
            "proof_purpose": self._first_text(row, "proof_purpose", "purpose", "fact_to_prove"),
            "original_or_copy": self._first_text(row, "original_or_copy"),
            "hash_or_checksum": self._first_text(row, "hash_or_checksum", "content_hash", "checksum", "sha256"),
            "authenticity_review": self._first_value(row, "authenticity_review", "authenticity_status"),
            "relevance_review": self._first_value(row, "relevance_review", "relevance_status"),
            "legality_review": self._first_value(row, "legality_review", "legality_status"),
            "confidentiality_level": self._first_text(row, "confidentiality_level", "visibility"),
        }

    def _integrity_item(self, row: Mapping[str, Any], index: int) -> dict[str, Any]:
        return {
            "evidence_id": self._safe_ref(
                self._first_text(row, "evidence_id", "evidence_no", "exhibit_number", "id"),
                index=index,
                prefix="EV",
            ),
            "source_id": self._first_text(row, "source_id", "source_anchor", "evidence_source", "source"),
            "proof_purpose": self._first_text(row, "proof_purpose", "purpose", "fact_to_prove"),
            "evidence_date": self._first_text(row, "evidence_date", "date", "event_date", "document_date"),
            "amount": self._first_value(row, "amount", "amount_yuan", "claimed_amount", "contract_amount"),
            "content_hash": self._first_text(row, "content_hash", "hash_or_checksum", "checksum", "sha256"),
            "file_name": self._redacted_label(index),
            "metadata": {
                "page_anchor_present": bool(self._first_text(row, "page_anchor", "page_range", "page_refs")),
                "three_factor_review_present": all(
                    self._first_value(row, key)
                    for key in ("authenticity_review", "relevance_review", "legality_review")
                ),
            },
        }

    def _review_actions(self, package_policy: dict[str, Any], bundle_integrity: dict[str, Any]) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for action in package_policy["review_actions"]:
            actions.append(
                {
                    "id": f"package-{action['id']}",
                    "source": "exhibit_package_policy",
                    "required_role": action["required_role"],
                    "action": action["action"],
                }
            )
        for index, action in enumerate(bundle_integrity["recommended_actions"], start=1):
            actions.append(
                {
                    "id": f"integrity-action-{index:03d}",
                    "source": "evidence_bundle_integrity",
                    "required_role": "lawyer_or_reviewer",
                    "action": action,
                }
            )
        return actions

    def _status(
        self,
        rows: list[dict[str, Any]],
        package_policy: dict[str, Any],
        bundle_integrity: dict[str, Any],
    ) -> str:
        if not rows:
            return "template"
        if package_policy["status"] == "blocked" or bundle_integrity["status"] == "blocked":
            return "blocked"
        if package_policy["status"] == "ready" and bundle_integrity["status"] == "ready":
            return "ready_for_export"
        return "review_required"

    def _safe_ref(
        self,
        value: str,
        *,
        index: int,
        prefix: str,
        allow_empty: bool = False,
    ) -> str:
        text = str(value or "").strip()
        if allow_empty and not text:
            return ""
        if text and SAFE_REF_PATTERN.fullmatch(text) and not SENSITIVE_VALUE_PATTERN.search(text):
            return text
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8] if text else f"{index:03d}"
        return f"{prefix}-{index:03d}-{digest}"

    def _redacted_label(self, index: int) -> str:
        return f"redacted-evidence-row-{index:03d}"

    def _first_text(self, row: Mapping[str, Any], *keys: str) -> str:
        value = self._first_value(row, *keys)
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()

    def _first_value(self, row: Mapping[str, Any], *keys: str) -> Any:
        for key in keys:
            value = row.get(key)
            if self._present(value):
                return value
        metadata = row.get("metadata")
        if isinstance(metadata, Mapping):
            for key in keys:
                value = metadata.get(key)
                if self._present(value):
                    return value
        return None

    def _present(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, tuple, set, dict)):
            return bool(value)
        return True


def preflight_contains_sensitive_text(payload: dict[str, Any]) -> bool:
    serialized = json.dumps(payload, ensure_ascii=False)
    return bool(SENSITIVE_VALUE_PATTERN.search(serialized))
