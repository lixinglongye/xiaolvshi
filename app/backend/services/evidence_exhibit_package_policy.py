from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExhibitSchemaField:
    name: str
    required: bool
    purpose: str
    example: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PackageCheckDefinition:
    id: str
    label: str
    required_before_export: bool
    product_gap_closed: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class EvidenceExhibitPackagePolicyService:
    """Evaluate evidence catalog and exhibit package readiness before delivery."""

    REQUIRED_CORE_FIELDS = ("exhibit_number", "proof_purpose", "source_anchor")
    REQUIRED_ANCHOR_FIELDS = ("attachment_number", "page_anchor")
    THREE_FACTOR_REVIEW_FIELDS = (
        "authenticity_review",
        "relevance_review",
        "legality_review",
    )
    PASS_REVIEW_VALUES = {"pass", "passed", "reviewed", "verified", "approved", "ok"}
    FAIL_REVIEW_VALUES = {"fail", "failed", "rejected", "invalid", "unlawful", "unrelated"}

    def build_policy(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        exhibits = self._exhibits(payload)
        blocking_issues = self._blocking_issues(exhibits)
        package_checks = self._package_checks(blocking_issues, exhibits)
        status = self._status(exhibits, blocking_issues)

        return {
            "status": status,
            "policy_id": "evidence-exhibit-package-policy-v1",
            "method": {
                "type": "deterministic-evidence-exhibit-package-policy",
                "notes": [
                    "The service evaluates exhibit metadata only and does not read uploaded files.",
                    "Use it before generating an evidence catalog, attachment bundle, or client delivery package.",
                    "Final export remains blocked until exhibit numbering, page anchors, proof purpose, and three-factor review pass.",
                ],
            },
            "summary": {
                "exhibit_count": len(exhibits),
                "blocking_issue_count": len(blocking_issues),
                "ready_for_export": status == "ready",
                "required_core_field_count": len(self.REQUIRED_CORE_FIELDS),
                "required_anchor_field_count": len(self.REQUIRED_ANCHOR_FIELDS),
                "three_factor_review_count": len(self.THREE_FACTOR_REVIEW_FIELDS),
                "export_manifest_field_count": len(self._export_manifest_fields()),
            },
            "exhibit_metadata_schema": [field.to_api() for field in self._schema_fields()],
            "package_checks": package_checks,
            "blocking_issues": blocking_issues,
            "review_actions": self._review_actions(blocking_issues, exhibits),
            "export_manifest_fields": self._export_manifest_fields(),
            "delivery_policy": [
                "Evidence and attachments are drafts until every exhibit has a stable number, proof purpose, source anchor, and page anchor.",
                "The catalog number, attachment number, and exported file name must stay aligned.",
                "Authenticity, relevance, and legality review must be recorded before any external package delivery.",
                "The export manifest must preserve the reviewed version, checksum list, page index, and reviewer decision.",
            ],
            "low_resource_validation_commands": [
                {
                    "id": "evidence-exhibit-package-policy-tests",
                    "command": "python -m pytest tests/test_evidence_exhibit_package_policy.py -q",
                    "resource_note": "Runs deterministic metadata tests only; no model call, OCR run, or large document fixture is required.",
                },
                {
                    "id": "evidence-exhibit-package-policy-diff-check",
                    "command": "git diff --check -- app/backend/services/evidence_exhibit_package_policy.py app/backend/tests/test_evidence_exhibit_package_policy.py docs/EVIDENCE_EXHIBIT_PACKAGE_POLICY.md",
                    "resource_note": "Expected result is no whitespace errors.",
                },
            ],
            "privacy_notes": [
                "Store exhibit IDs, package IDs, page ranges, review states, checksums, and redacted labels instead of raw client materials.",
                "Avoid placing private party details, full file paths, original document text, or model output in policy payloads.",
                "Export manifests should reference reviewed package artifacts by ID and checksum, with access controlled by case role.",
            ],
            "future_api": {
                "suggested_endpoint": "POST /api/v1/evidence/exhibit-package/policy",
                "integration_note": "Call after evidence intake and before catalog generation or bundle export.",
            },
        }

    def _schema_fields(self) -> tuple[ExhibitSchemaField, ...]:
        return (
            ExhibitSchemaField(
                name="exhibit_number",
                required=True,
                purpose="Stable catalog identifier used in pleadings, catalog rows, and attachment names.",
                example="E-001",
            ),
            ExhibitSchemaField(
                name="attachment_number",
                required=True,
                purpose="Bundle ordering value that maps catalog rows to exported attachment files.",
                example="A-001",
            ),
            ExhibitSchemaField(
                name="title",
                required=True,
                purpose="Short redacted exhibit label for reviewers and exported catalogs.",
                example="Signed contract excerpt",
            ),
            ExhibitSchemaField(
                name="source_anchor",
                required=True,
                purpose="Internal reference to the intake record, source file ID, or evidence graph node.",
                example="source:upload-001",
            ),
            ExhibitSchemaField(
                name="page_anchor",
                required=True,
                purpose="Page or range anchor that lets reviewers jump from catalog row to the cited attachment page.",
                example="pages 3-5",
            ),
            ExhibitSchemaField(
                name="proof_purpose",
                required=True,
                purpose="Fact, disputed issue, claim element, or risk item the exhibit is offered to prove.",
                example="Proves delivery date and contract performance baseline.",
            ),
            ExhibitSchemaField(
                name="source_type",
                required=False,
                purpose="Document, message export, photo, transaction record, public record, or other source class.",
                example="signed_document",
            ),
            ExhibitSchemaField(
                name="original_or_copy",
                required=False,
                purpose="Marks whether the exhibit is an original, copy, scan, transcript, or screenshot.",
                example="copy",
            ),
            ExhibitSchemaField(
                name="hash_or_checksum",
                required=False,
                purpose="Digest used to confirm exported attachment integrity.",
                example="sha256:<redacted>",
            ),
            ExhibitSchemaField(
                name="authenticity_review",
                required=True,
                purpose="Reviewer result for whether the source, origin, and chain details are supportable.",
                example="passed",
            ),
            ExhibitSchemaField(
                name="relevance_review",
                required=True,
                purpose="Reviewer result for whether the exhibit connects to a fact, claim, defense, or dispute.",
                example="passed",
            ),
            ExhibitSchemaField(
                name="legality_review",
                required=True,
                purpose="Reviewer result for whether collection and use are acceptable for the intended delivery.",
                example="passed",
            ),
            ExhibitSchemaField(
                name="confidentiality_level",
                required=False,
                purpose="Delivery visibility label such as internal, client-share, court-file, or restricted.",
                example="internal",
            ),
        )

    def _check_definitions(self) -> tuple[PackageCheckDefinition, ...]:
        return (
            PackageCheckDefinition(
                id="numbering-complete",
                label="Catalog and attachment numbering",
                required_before_export=True,
                product_gap_closed="Prevents unnamed or mismatched attachments in exported evidence packages.",
            ),
            PackageCheckDefinition(
                id="page-anchors-complete",
                label="Page anchors",
                required_before_export=True,
                product_gap_closed="Lets reviewers and recipients jump from catalog row to cited pages.",
            ),
            PackageCheckDefinition(
                id="proof-purpose-complete",
                label="Proof purpose",
                required_before_export=True,
                product_gap_closed="Links every exhibit to a fact, dispute, claim element, defense, or risk item.",
            ),
            PackageCheckDefinition(
                id="source-anchors-complete",
                label="Source anchors",
                required_before_export=True,
                product_gap_closed="Keeps each exhibit traceable to intake records or evidence graph nodes.",
            ),
            PackageCheckDefinition(
                id="three-factor-review-complete",
                label="Authenticity, relevance, and legality review",
                required_before_export=True,
                product_gap_closed="Makes the three-factor evidence review a hard delivery gate.",
            ),
            PackageCheckDefinition(
                id="export-manifest-complete",
                label="Export manifest",
                required_before_export=True,
                product_gap_closed="Records reviewed version, checksums, page index, review status, and delivery channel.",
            ),
        )

    def _package_checks(self, blocking_issues: list[dict[str, Any]], exhibits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        issue_ids_by_check: dict[str, list[str]] = {definition.id: [] for definition in self._check_definitions()}
        for issue in blocking_issues:
            check_id = issue["check_id"]
            issue_ids_by_check.setdefault(check_id, []).append(issue["id"])

        checks: list[dict[str, Any]] = []
        for definition in self._check_definitions():
            issue_ids = issue_ids_by_check.get(definition.id, [])
            checks.append(
                {
                    **definition.to_api(),
                    "status": "template" if not exhibits else ("blocked" if issue_ids else "pass"),
                    "blocking_issue_ids": issue_ids,
                }
            )
        return checks

    def _blocking_issues(self, exhibits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        numbers: dict[str, int] = {}

        for index, exhibit in enumerate(exhibits, start=1):
            exhibit_ref = self._exhibit_ref(exhibit, index)
            for field in self.REQUIRED_CORE_FIELDS:
                if not _present(exhibit.get(field)):
                    issues.append(
                        self._issue(
                            issue_id=f"{exhibit_ref}-missing-{field}",
                            exhibit_ref=exhibit_ref,
                            check_id=self._check_id_for_field(field),
                            field=field,
                            message=f"Exhibit {exhibit_ref} is missing required field {field}.",
                            reviewer_action=f"Add {field} before package export.",
                        )
                    )

            for field in self.REQUIRED_ANCHOR_FIELDS:
                if not _present(exhibit.get(field)):
                    issues.append(
                        self._issue(
                            issue_id=f"{exhibit_ref}-missing-{field}",
                            exhibit_ref=exhibit_ref,
                            check_id="page-anchors-complete" if field == "page_anchor" else "numbering-complete",
                            field=field,
                            message=f"Exhibit {exhibit_ref} is missing required anchor field {field}.",
                            reviewer_action=f"Add {field} so the catalog, attachment bundle, and page index stay aligned.",
                        )
                    )

            number = _text(exhibit.get("exhibit_number"))
            if number:
                numbers[number] = numbers.get(number, 0) + 1

            for field in self.THREE_FACTOR_REVIEW_FIELDS:
                review_status = self._review_status(exhibit.get(field))
                if review_status not in self.PASS_REVIEW_VALUES:
                    severity = "failed" if review_status in self.FAIL_REVIEW_VALUES else "missing_or_pending"
                    issues.append(
                        self._issue(
                            issue_id=f"{exhibit_ref}-{field}-{severity}",
                            exhibit_ref=exhibit_ref,
                            check_id="three-factor-review-complete",
                            field=field,
                            message=f"Exhibit {exhibit_ref} has not passed {field}.",
                            reviewer_action=f"Record a passing {field} result or remove the exhibit from the delivery package.",
                        )
                    )

        duplicate_numbers = {number for number, count in numbers.items() if count > 1}
        for number in sorted(duplicate_numbers):
            issues.append(
                self._issue(
                    issue_id=f"duplicate-exhibit-number-{number}",
                    exhibit_ref=number,
                    check_id="numbering-complete",
                    field="exhibit_number",
                    message=f"Exhibit number {number} appears more than once.",
                    reviewer_action="Assign unique exhibit numbers before export.",
                )
            )

        return issues

    def _issue(
        self,
        *,
        issue_id: str,
        exhibit_ref: str,
        check_id: str,
        field: str,
        message: str,
        reviewer_action: str,
    ) -> dict[str, Any]:
        return {
            "id": issue_id,
            "severity": "blocking",
            "exhibit_ref": exhibit_ref,
            "check_id": check_id,
            "field": field,
            "message": message,
            "reviewer_action": reviewer_action,
        }

    def _review_actions(self, blocking_issues: list[dict[str, Any]], exhibits: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not exhibits:
            return [
                {
                    "id": "collect-exhibit-metadata",
                    "label": "Collect exhibit metadata",
                    "required_role": "lawyer_or_reviewer",
                    "action": "Create exhibit rows with numbers, proof purpose, source anchors, page anchors, and three-factor review fields.",
                }
            ]

        actions_by_check = {
            "numbering-complete": "Fix exhibit and attachment numbering so every row maps to exactly one exported file.",
            "page-anchors-complete": "Add page anchors or ranges for every cited attachment.",
            "proof-purpose-complete": "Tie proof purpose to a fact, dispute, claim element, defense, or risk item.",
            "source-anchors-complete": "Link each exhibit to intake source records or evidence graph nodes.",
            "three-factor-review-complete": "Complete authenticity, relevance, and legality review before delivery.",
            "export-manifest-complete": "Regenerate manifest after all metadata and review gates pass.",
        }
        blocked_check_ids = []
        for issue in blocking_issues:
            if issue["check_id"] not in blocked_check_ids:
                blocked_check_ids.append(issue["check_id"])

        if not blocked_check_ids:
            return [
                {
                    "id": "approve-export-manifest",
                    "label": "Approve export manifest",
                    "required_role": "lawyer_or_reviewer",
                    "action": "Confirm reviewed package version, page index, checksums, and delivery channel.",
                }
            ]

        return [
            {
                "id": f"review-{check_id}",
                "label": check_id.replace("-", " "),
                "required_role": "lawyer_or_reviewer",
                "action": actions_by_check[check_id],
            }
            for check_id in blocked_check_ids
        ]

    def _export_manifest_fields(self) -> list[dict[str, Any]]:
        return [
            {"name": "package_id", "required": True, "purpose": "Stable ID for the exported evidence package."},
            {"name": "case_id", "required": True, "purpose": "Case workspace boundary for access and audit controls."},
            {"name": "package_version", "required": True, "purpose": "Reviewed package version used for delivery."},
            {"name": "generated_at", "required": True, "purpose": "Timestamp for the manifest generation event."},
            {"name": "review_status", "required": True, "purpose": "Final package review result before export."},
            {"name": "reviewer_id", "required": True, "purpose": "Reviewer identifier for approval traceability."},
            {"name": "exhibit_count", "required": True, "purpose": "Number of exhibits included in the package."},
            {"name": "exhibit_numbers", "required": True, "purpose": "Ordered exhibit number list."},
            {"name": "attachment_files", "required": True, "purpose": "Attachment file IDs, names, order, and checksums."},
            {"name": "page_anchor_index", "required": True, "purpose": "Mapping from exhibit number to page anchors or ranges."},
            {"name": "proof_purpose_index", "required": True, "purpose": "Mapping from exhibit number to proof purpose."},
            {"name": "three_factor_review_summary", "required": True, "purpose": "Authenticity, relevance, and legality results by exhibit."},
            {"name": "confidentiality_map", "required": True, "purpose": "Visibility labels used by delivery and export controls."},
            {"name": "delivery_channel", "required": True, "purpose": "Court filing, client delivery, counterparty delivery, or internal archive."},
            {"name": "retention_rule_id", "required": True, "purpose": "Retention policy reference for the delivered package."},
        ]

    def _exhibits(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        exhibits = payload.get("exhibits")
        if not isinstance(exhibits, list):
            return []
        return [item for item in exhibits if isinstance(item, dict)]

    def _status(self, exhibits: list[dict[str, Any]], blocking_issues: list[dict[str, Any]]) -> str:
        if not exhibits:
            return "template"
        if blocking_issues:
            return "blocked"
        return "ready"

    def _check_id_for_field(self, field: str) -> str:
        if field == "exhibit_number":
            return "numbering-complete"
        if field == "proof_purpose":
            return "proof-purpose-complete"
        if field == "source_anchor":
            return "source-anchors-complete"
        return "export-manifest-complete"

    def _exhibit_ref(self, exhibit: dict[str, Any], index: int) -> str:
        return _text(exhibit.get("exhibit_number")) or f"row-{index:03d}"

    def _review_status(self, value: Any) -> str:
        if isinstance(value, dict):
            value = value.get("status") or value.get("result") or value.get("decision")
        return _text(value).lower()


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()
