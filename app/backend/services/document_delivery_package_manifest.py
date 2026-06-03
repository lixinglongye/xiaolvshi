from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SUPPORTED_EXPORT_FORMATS = ("docx", "pdf", "markdown", "json")

PASS_REVIEW_VALUES = {
    "accepted",
    "approved",
    "ok",
    "pass",
    "passed",
    "reviewed",
    "signed",
    "verified",
}
SOURCE_COMPLETE_VALUES = {
    "complete",
    "completed",
    "pass",
    "passed",
    "supported",
    "verified",
    "approved",
}
MISSING_FACT_CLEAR_VALUES = {
    "none",
    "resolved",
    "cleared",
    "not_applicable",
    "not_required",
    "approved_with_caveat",
}
RESOLVED_FACT_VALUES = {
    "accepted",
    "approved",
    "cleared",
    "closed",
    "not_applicable",
    "not_required",
    "resolved",
    "waived",
}

RISK_MESSAGES = {
    "package_identity_missing": "Package ID, case ID, current version, or delivery channel is missing.",
    "documents_missing": "The delivery package does not list any legal document artifacts.",
    "document_metadata_incomplete": "One or more document rows lack ID, type, version, or export format metadata.",
    "source_support_missing": "Source support metadata is absent or incomplete.",
    "source_support_not_complete": "Source support has not been marked complete.",
    "source_anchor_missing": "No citation, evidence link, or source anchor count is recorded.",
    "unsupported_claims_present": "The package still contains unsupported claims or conclusions.",
    "missing_fact_manifest_missing": "Missing-fact review metadata is absent or incomplete.",
    "missing_fact_status_not_clear": "Missing-fact review is not cleared for final delivery.",
    "unresolved_missing_facts": "Unresolved missing facts remain in the final package metadata.",
    "lawyer_review_missing": "Lawyer review metadata is absent or incomplete.",
    "lawyer_review_not_approved": "A responsible lawyer has not approved the package.",
    "lawyer_review_version_mismatch": "The lawyer-reviewed version does not match the package version.",
    "client_notice_missing": "The client transparency notice is absent or incomplete.",
    "client_notice_not_visible": "The client transparency notice is not marked visible to the client.",
    "risk_notice_missing": "Risk notice content is missing from the client-visible package.",
    "scope_limits_missing": "Scope limits or assumptions are missing from the client-visible package.",
    "export_format_missing": "Export format metadata is absent or incomplete.",
    "unsupported_export_format": "The requested export format is not in the supported local format list.",
    "export_version_not_locked": "The export version is not locked to the reviewed package.",
    "version_notes_missing": "Version notes are absent or incomplete.",
    "version_notes_version_mismatch": "Version notes do not match the current package version.",
}


@dataclass(frozen=True)
class ManifestSectionDefinition:
    id: str
    title: str
    owner: str
    required_before_delivery: bool
    required_fields: tuple[str, ...]
    purpose: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_fields"] = list(self.required_fields)
        return data


class DocumentDeliveryPackageManifestService:
    """Build a deterministic local manifest for final legal-document delivery packages."""

    def build_manifest(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload if isinstance(payload, dict) else {}
        sections = self._manifest_sections(payload)
        risk_flags = self._risk_flags(sections)
        status = self._overall_status(payload, sections, risk_flags)

        return {
            "status": status,
            "manifest_id": "document-delivery-package-manifest-v1",
            "method": {
                "type": "deterministic-local-document-delivery-manifest",
                "notes": [
                    "Evaluates delivery-package metadata only; it does not read files, call models, run OCR, or use network services.",
                    "Designed to run after drafting, source support, lawyer review, client transparency checks, and export preparation.",
                    "The output is safe for audit and integration work because it returns states, counts, field names, and risk codes only.",
                ],
            },
            "summary": {
                "section_count": len(sections),
                "pass_count": self._count_status(sections, "pass"),
                "template_count": self._count_status(sections, "template"),
                "fail_count": self._count_status(sections, "fail"),
                "risk_flag_count": len(risk_flags),
                "blocking_risk_count": sum(1 for flag in risk_flags if flag["severity"] == "blocking"),
                "document_count": self._document_count(payload),
                "supported_export_formats": list(SUPPORTED_EXPORT_FORMATS),
                "required_manifest_sections": [section.id for section in self._section_definitions()],
                "ready_for_delivery": status == "ready",
                "raw_payload_echoed": False,
            },
            "manifest_sections": sections,
            "risk_flags": risk_flags,
            "recommended_actions": self._recommended_actions(payload, sections, risk_flags),
            "privacy_note": (
                "This manifest service keeps delivery checks metadata-only. Pass redacted IDs, booleans, counts, "
                "timestamps, version IDs, format names, review states, and checksum labels; keep party details, "
                "full document text, local file paths, private notes, API keys, and login auth data in protected case storage."
            ),
            "validation_commands": [
                {
                    "id": "document-delivery-package-manifest-tests",
                    "command": "python -m pytest tests/test_document_delivery_package_manifest.py -q",
                    "resource_note": "Runs deterministic local tests only; no network, model call, OCR, or large fixture is required.",
                },
                {
                    "id": "document-delivery-package-manifest-compile",
                    "command": "python -m compileall services/document_delivery_package_manifest.py",
                    "resource_note": "Checks syntax and import health for the local manifest service.",
                },
            ],
        }

    def _section_definitions(self) -> tuple[ManifestSectionDefinition, ...]:
        return (
            ManifestSectionDefinition(
                id="package-identity",
                title="Package identity and delivery boundary",
                owner="legal_operations",
                required_before_delivery=True,
                required_fields=(
                    "package.package_id",
                    "package.case_id",
                    "package.current_version_id",
                    "package.delivery_channel",
                ),
                purpose="Creates the stable package envelope used for audit, access control, and delivery tracking.",
            ),
            ManifestSectionDefinition(
                id="documents",
                title="Included legal documents",
                owner="case_owner",
                required_before_delivery=True,
                required_fields=(
                    "documents[].document_id",
                    "documents[].document_type",
                    "documents[].version_id",
                    "documents[].export_formats",
                ),
                purpose="Confirms which reviewed legal document artifacts are included in the final package.",
            ),
            ManifestSectionDefinition(
                id="source-support",
                title="Source support and citation coverage",
                owner="responsible_lawyer",
                required_before_delivery=True,
                required_fields=(
                    "source_support.status",
                    "source_support.source_count",
                    "source_support.unsupported_claim_count",
                ),
                purpose="Keeps client-facing conclusions traceable to citations, evidence links, or explicit caveats.",
            ),
            ManifestSectionDefinition(
                id="missing-facts",
                title="Missing-fact review",
                owner="case_owner",
                required_before_delivery=True,
                required_fields=("missing_facts.status", "missing_facts.items"),
                purpose="Records whether required facts are resolved, waived, or still blocking final delivery.",
            ),
            ManifestSectionDefinition(
                id="lawyer-review",
                title="Lawyer review and approval",
                owner="responsible_lawyer",
                required_before_delivery=True,
                required_fields=(
                    "lawyer_review.status",
                    "lawyer_review.reviewer_id",
                    "lawyer_review.reviewed_at",
                    "lawyer_review.reviewed_version_id",
                ),
                purpose="Links delivery to the exact lawyer-reviewed package version.",
            ),
            ManifestSectionDefinition(
                id="client-transparency-notice",
                title="Client transparency notice",
                owner="case_owner",
                required_before_delivery=True,
                required_fields=(
                    "client_transparency.notice_present",
                    "client_transparency.client_visible",
                    "client_transparency.risk_notice_included",
                    "client_transparency.scope_limits_included",
                ),
                purpose="Makes risk, assumptions, limitations, and delivery context visible before client release.",
            ),
            ManifestSectionDefinition(
                id="export-formats",
                title="Export format and version lock",
                owner="legal_operations",
                required_before_delivery=True,
                required_fields=("export.formats", "export.final_format", "export.version_locked"),
                purpose="Confirms the exported file types are supported and tied to the reviewed version.",
            ),
            ManifestSectionDefinition(
                id="version-notes",
                title="Version notes and change summary",
                owner="responsible_lawyer",
                required_before_delivery=True,
                required_fields=(
                    "version_notes.current_version_id",
                    "version_notes.summary_present",
                    "version_notes.generated_at",
                ),
                purpose="Preserves the client-visible version explanation for the delivered package.",
            ),
        )

    def _manifest_sections(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        evaluators = {
            "package-identity": self._package_identity_section,
            "documents": self._documents_section,
            "source-support": self._source_support_section,
            "missing-facts": self._missing_facts_section,
            "lawyer-review": self._lawyer_review_section,
            "client-transparency-notice": self._client_transparency_section,
            "export-formats": self._export_formats_section,
            "version-notes": self._version_notes_section,
        }
        sections: list[dict[str, Any]] = []
        for definition in self._section_definitions():
            if not payload:
                sections.append(self._template_section(definition))
                continue
            sections.append(evaluators[definition.id](definition, payload))
        return sections

    def _package_identity_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        package = _first_section(payload, "package", "manifest", "delivery_package")
        values = {
            "package.package_id": _first_present(package.get("package_id"), package.get("id"), payload.get("package_id")),
            "package.case_id": _first_present(package.get("case_id"), payload.get("case_id")),
            "package.current_version_id": self._current_version_id(payload),
            "package.delivery_channel": _first_present(
                package.get("delivery_channel"),
                package.get("channel"),
                payload.get("delivery_channel"),
            ),
        }
        missing = [field for field, value in values.items() if not _present(value)]
        return self._section_result(
            definition,
            status="fail" if missing else "pass",
            missing_fields=missing,
            risk_codes=["package_identity_missing"] if missing else [],
            notes=(
                ["Package identity contains case, version, and delivery boundary metadata."]
                if not missing
                else ["Add package ID, case ID, current version, and delivery channel before final delivery."]
            ),
            observed={
                "has_package_id": _present(values["package.package_id"]),
                "has_case_id": _present(values["package.case_id"]),
                "has_current_version_id": _present(values["package.current_version_id"]),
                "has_delivery_channel": _present(values["package.delivery_channel"]),
            },
        )

    def _documents_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        documents = self._documents(payload)
        row_issues: list[dict[str, Any]] = []
        missing_field_names: set[str] = set()

        for index, document in enumerate(documents, start=1):
            row_missing: list[str] = []
            field_values = {
                "documents[].document_id": _first_present(document.get("document_id"), document.get("id")),
                "documents[].document_type": _first_present(document.get("document_type"), document.get("type")),
                "documents[].version_id": _first_present(
                    document.get("version_id"),
                    document.get("current_version_id"),
                    document.get("reviewed_version_id"),
                ),
                "documents[].export_formats": _first_present(
                    document.get("export_formats"),
                    document.get("formats"),
                    document.get("export_format"),
                ),
            }
            for field, value in field_values.items():
                if not _present(value):
                    row_missing.append(field)
                    missing_field_names.add(field)
            if row_missing:
                row_issues.append({"row": index, "missing_fields": row_missing})

        if not documents:
            missing = ["documents"]
            risk_codes = ["documents_missing"]
        else:
            missing = sorted(missing_field_names)
            risk_codes = ["document_metadata_incomplete"] if row_issues else []

        return self._section_result(
            definition,
            status="fail" if missing else "pass",
            missing_fields=missing,
            risk_codes=risk_codes,
            notes=(
                ["All listed legal documents include ID, type, version, and format metadata."]
                if not missing
                else ["List every deliverable document with stable ID, document type, reviewed version, and export formats."]
            ),
            observed={
                "document_count": len(documents),
                "complete_document_count": len(documents) - len(row_issues),
                "row_issue_count": len(row_issues),
                "row_issues": row_issues,
            },
        )

    def _source_support_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        source = _first_section(payload, "source_support", "citation_support", "evidence_support")
        status_value = _text(_first_present(source.get("status"), source.get("review_status"))).lower()
        complete_flag = _truthy(
            _first_present(
                source.get("complete"),
                source.get("source_support_complete"),
                source.get("all_claims_supported"),
            )
        )
        support_complete = complete_flag or status_value in SOURCE_COMPLETE_VALUES
        unsupported_count_value = _first_present(
            source.get("unsupported_claim_count"),
            source.get("unsupported_count"),
            source.get("open_claim_count"),
        )
        unsupported_count = _safe_int(unsupported_count_value, 0)
        source_count = self._source_count(source)

        missing: list[str] = []
        risk_codes: list[str] = []
        if not source:
            missing.extend(definition.required_fields)
            risk_codes.append("source_support_missing")
        else:
            if not status_value and not complete_flag:
                missing.append("source_support.status")
                risk_codes.append("source_support_not_complete")
            elif not support_complete:
                risk_codes.append("source_support_not_complete")
            if not _present(unsupported_count_value):
                missing.append("source_support.unsupported_claim_count")
                risk_codes.append("source_support_missing")
            if source_count <= 0:
                missing.append("source_support.source_count")
                risk_codes.append("source_anchor_missing")
        if unsupported_count > 0:
            risk_codes.append("unsupported_claims_present")

        risk_codes = _dedupe(risk_codes)
        return self._section_result(
            definition,
            status="fail" if missing or risk_codes else "pass",
            missing_fields=sorted(set(missing)),
            risk_codes=risk_codes,
            notes=(
                ["Source support is complete and no unsupported claims are recorded."]
                if not missing and not risk_codes
                else ["Complete citation or evidence support and remove unsupported claims before delivery."]
            ),
            observed={
                "source_count": source_count,
                "unsupported_claim_count": unsupported_count,
                "source_support_complete": support_complete,
            },
        )

    def _missing_facts_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        fact_section = _first_section(payload, "missing_facts", "missing_fact_review", "fact_gaps")
        fact_items_value = _first_list_value(
            fact_section.get("items"),
            fact_section.get("facts"),
            fact_section.get("missing_required_facts"),
            payload.get("missing_required_facts"),
            payload.get("missing_facts") if isinstance(payload.get("missing_facts"), list) else None,
        )
        fact_items = _list_of_dicts(fact_items_value)
        status_value = _text(
            _first_present(fact_section.get("status"), fact_section.get("review_status"), fact_section.get("decision"))
        ).lower()
        explicit_unresolved = _first_present(fact_section.get("unresolved_count"), fact_section.get("open_count"))
        unresolved_count = (
            _safe_int(explicit_unresolved, 0)
            if _present(explicit_unresolved)
            else sum(1 for item in fact_items if not self._fact_item_resolved(item))
        )

        missing: list[str] = []
        risk_codes: list[str] = []
        if not fact_section and not isinstance(payload.get("missing_facts"), list):
            missing.extend(definition.required_fields)
            risk_codes.append("missing_fact_manifest_missing")
        else:
            if not status_value:
                missing.append("missing_facts.status")
                risk_codes.append("missing_fact_status_not_clear")
            elif status_value not in MISSING_FACT_CLEAR_VALUES:
                risk_codes.append("missing_fact_status_not_clear")
            if not isinstance(fact_items_value, list):
                missing.append("missing_facts.items")
                risk_codes.append("missing_fact_manifest_missing")
        if unresolved_count > 0:
            risk_codes.append("unresolved_missing_facts")

        risk_codes = _dedupe(risk_codes)
        return self._section_result(
            definition,
            status="fail" if missing or risk_codes else "pass",
            missing_fields=sorted(set(missing)),
            risk_codes=risk_codes,
            notes=(
                ["Missing-fact review is clear for delivery."]
                if not missing and not risk_codes
                else ["Resolve, waive, or explicitly clear missing facts before final package delivery."]
            ),
            observed={
                "missing_fact_count": len(fact_items),
                "unresolved_fact_count": unresolved_count,
                "review_status": status_value or None,
            },
        )

    def _lawyer_review_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        review = _first_section(payload, "lawyer_review", "legal_review", "review")
        status_value = _text(_first_present(review.get("status"), review.get("decision"), review.get("result"))).lower()
        reviewed_version = _text(
            _first_present(
                review.get("reviewed_version_id"),
                review.get("package_version_id"),
                review.get("version_id"),
            )
        )
        current_version = _text(self._current_version_id(payload))
        values = {
            "lawyer_review.status": status_value,
            "lawyer_review.reviewer_id": _first_present(review.get("reviewer_id"), review.get("lawyer_id")),
            "lawyer_review.reviewed_at": _first_present(review.get("reviewed_at"), review.get("approved_at")),
            "lawyer_review.reviewed_version_id": reviewed_version,
        }

        missing = [field for field, value in values.items() if not _present(value)]
        risk_codes: list[str] = []
        if not review:
            risk_codes.append("lawyer_review_missing")
        if status_value and status_value not in PASS_REVIEW_VALUES:
            risk_codes.append("lawyer_review_not_approved")
        if current_version and reviewed_version and current_version != reviewed_version:
            risk_codes.append("lawyer_review_version_mismatch")
        if missing and "lawyer_review_missing" not in risk_codes:
            risk_codes.append("lawyer_review_missing")

        risk_codes = _dedupe(risk_codes)
        return self._section_result(
            definition,
            status="fail" if missing or risk_codes else "pass",
            missing_fields=missing,
            risk_codes=risk_codes,
            notes=(
                ["Lawyer approval is recorded for the current package version."]
                if not missing and not risk_codes
                else ["Block delivery until a responsible lawyer approves the exact current package version."]
            ),
            observed={
                "review_status": status_value or None,
                "reviewed_version_matches_package": bool(current_version and reviewed_version and current_version == reviewed_version),
            },
        )

    def _client_transparency_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        notice = _first_section(payload, "client_transparency", "client_transparency_notice", "client_notice")
        values = {
            "client_transparency.notice_present": _truthy(
                _first_present(notice.get("notice_present"), notice.get("present"), notice.get("summary_present"))
            ),
            "client_transparency.client_visible": _truthy(
                _first_present(notice.get("client_visible"), notice.get("visible_to_client"))
            ),
            "client_transparency.risk_notice_included": _truthy(
                _first_present(notice.get("risk_notice_included"), notice.get("risk_notice_present"))
            ),
            "client_transparency.scope_limits_included": _truthy(
                _first_present(
                    notice.get("scope_limits_included"),
                    notice.get("scope_limits_present"),
                    notice.get("assumptions_included"),
                )
            ),
        }
        missing = [field for field, passed in values.items() if not passed]
        risk_codes: list[str] = []
        if not notice:
            risk_codes.append("client_notice_missing")
        else:
            if not values["client_transparency.notice_present"]:
                risk_codes.append("client_notice_missing")
            if not values["client_transparency.client_visible"]:
                risk_codes.append("client_notice_not_visible")
            if not values["client_transparency.risk_notice_included"]:
                risk_codes.append("risk_notice_missing")
            if not values["client_transparency.scope_limits_included"]:
                risk_codes.append("scope_limits_missing")

        risk_codes = _dedupe(risk_codes)
        return self._section_result(
            definition,
            status="fail" if missing or risk_codes else "pass",
            missing_fields=missing,
            risk_codes=risk_codes,
            notes=(
                ["Client transparency notice is present, visible, and includes risk and scope limits."]
                if not missing and not risk_codes
                else ["Show client-visible risk, assumptions, and scope-limit notice before delivery."]
            ),
            observed={
                "notice_present": values["client_transparency.notice_present"],
                "client_visible": values["client_transparency.client_visible"],
                "risk_notice_included": values["client_transparency.risk_notice_included"],
                "scope_limits_included": values["client_transparency.scope_limits_included"],
            },
        )

    def _export_formats_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        export = _first_section(payload, "export", "delivery_export", "export_manifest")
        formats = _formats(
            _first_present(export.get("formats"), export.get("export_formats"), payload.get("export_formats"))
        )
        final_format = _text(
            _first_present(
                export.get("final_format"),
                export.get("export_format"),
                payload.get("export_format"),
                formats[0] if len(formats) == 1 else None,
            )
        ).lower()
        version_locked_value = _first_present(export.get("version_locked"), payload.get("version_locked"))
        version_locked = _truthy(version_locked_value)
        all_formats = _dedupe([*formats, final_format] if final_format else formats)
        unsupported = [item for item in all_formats if item not in SUPPORTED_EXPORT_FORMATS]

        missing: list[str] = []
        risk_codes: list[str] = []
        if not formats:
            missing.append("export.formats")
            risk_codes.append("export_format_missing")
        if not final_format:
            missing.append("export.final_format")
            risk_codes.append("export_format_missing")
        if not _present(version_locked_value):
            missing.append("export.version_locked")
            risk_codes.append("export_version_not_locked")
        elif not version_locked:
            risk_codes.append("export_version_not_locked")
        if unsupported:
            risk_codes.append("unsupported_export_format")

        risk_codes = _dedupe(risk_codes)
        return self._section_result(
            definition,
            status="fail" if missing or risk_codes else "pass",
            missing_fields=missing,
            risk_codes=risk_codes,
            notes=(
                ["Export formats are supported and the export version is locked."]
                if not missing and not risk_codes
                else ["Choose a supported format and lock export to the reviewed package version."]
            ),
            observed={
                "formats": formats,
                "final_format": final_format or None,
                "unsupported_formats": unsupported,
                "version_locked": version_locked,
            },
        )

    def _version_notes_section(
        self, definition: ManifestSectionDefinition, payload: dict[str, Any]
    ) -> dict[str, Any]:
        notes = _first_section(payload, "version_notes", "release_notes", "change_notes")
        current_version = _text(self._current_version_id(payload))
        note_version = _text(
            _first_present(notes.get("current_version_id"), notes.get("package_version_id"), notes.get("version_id"))
        )
        previous_version = _text(_first_present(notes.get("previous_version_id"), notes.get("base_version_id")))
        summary_present = _truthy(notes.get("summary_present")) or _present(
            _first_present(notes.get("summary"), notes.get("change_summary"), notes.get("notes"))
        )
        generated_at = _first_present(notes.get("generated_at"), notes.get("prepared_at"), notes.get("created_at"))
        version_matches = bool(current_version and note_version and current_version == note_version)

        missing: list[str] = []
        risk_codes: list[str] = []
        if not notes:
            missing.extend(definition.required_fields)
            risk_codes.append("version_notes_missing")
        else:
            if not note_version:
                missing.append("version_notes.current_version_id")
                risk_codes.append("version_notes_missing")
            if not summary_present:
                missing.append("version_notes.summary_present")
                risk_codes.append("version_notes_missing")
            if not _present(generated_at):
                missing.append("version_notes.generated_at")
                risk_codes.append("version_notes_missing")
            if current_version and note_version and current_version != note_version:
                risk_codes.append("version_notes_version_mismatch")

        risk_codes = _dedupe(risk_codes)
        return self._section_result(
            definition,
            status="fail" if missing or risk_codes else "pass",
            missing_fields=sorted(set(missing)),
            risk_codes=risk_codes,
            notes=(
                ["Version notes describe the current package version."]
                if not missing and not risk_codes
                else ["Generate version notes that match the current package version before client delivery."]
            ),
            observed={
                "has_previous_version": bool(previous_version),
                "summary_present": summary_present,
                "current_version_matches_package": version_matches,
            },
        )

    def _template_section(self, definition: ManifestSectionDefinition) -> dict[str, Any]:
        return self._section_result(
            definition,
            status="template",
            missing_fields=list(definition.required_fields),
            risk_codes=[],
            notes=["Submit redacted delivery-package metadata to evaluate this manifest section."],
            observed={},
        )

    def _section_result(
        self,
        definition: ManifestSectionDefinition,
        *,
        status: str,
        missing_fields: list[str],
        risk_codes: list[str],
        notes: list[str],
        observed: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **definition.to_api(),
            "status": status,
            "passed": status == "pass",
            "missing_fields": missing_fields,
            "risk_codes": risk_codes,
            "notes": notes,
            "observed": observed,
        }

    def _risk_flags(self, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        flags: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for section in sections:
            for code in section["risk_codes"]:
                key = (section["id"], code)
                if key in seen:
                    continue
                seen.add(key)
                flags.append(
                    {
                        "id": code,
                        "section_id": section["id"],
                        "severity": "blocking" if section["required_before_delivery"] else "advisory",
                        "message": RISK_MESSAGES.get(code, "Delivery package manifest risk detected."),
                        "required_before_delivery": section["required_before_delivery"],
                    }
                )
        return flags

    def _recommended_actions(
        self,
        payload: dict[str, Any],
        sections: list[dict[str, Any]],
        risk_flags: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not payload:
            return [
                {
                    "id": "connect-delivery-package-metadata",
                    "priority": "medium",
                    "owner": "product",
                    "action": "Pass redacted package, document, source support, missing-fact, review, notice, export, and version-note metadata into this service.",
                    "missing_fields": ["payload"],
                    "risk_codes": ["manifest_template_payload_missing"],
                }
            ]

        if not risk_flags:
            return [
                {
                    "id": "approve-delivery-manifest",
                    "priority": "normal",
                    "owner": "responsible_lawyer",
                    "action": "Approve the manifest and archive the package ID, version ID, export formats, review state, and delivery channel.",
                    "missing_fields": [],
                    "risk_codes": [],
                }
            ]

        actions: list[dict[str, Any]] = []
        for section in sections:
            if section["status"] == "pass":
                continue
            actions.append(
                {
                    "id": f"resolve-{section['id']}",
                    "priority": "high" if section["required_before_delivery"] else "medium",
                    "owner": section["owner"],
                    "action": self._action_for_section(section["id"]),
                    "missing_fields": section["missing_fields"],
                    "risk_codes": section["risk_codes"],
                }
            )
        return actions

    def _action_for_section(self, section_id: str) -> str:
        actions = {
            "package-identity": "Complete the package envelope with stable case, package, version, and delivery-channel metadata.",
            "documents": "Add every final legal document artifact with ID, type, reviewed version, and export format metadata.",
            "source-support": "Finish source support so every conclusion is backed by citations, evidence links, or explicit caveats.",
            "missing-facts": "Resolve or clear missing facts before final delivery, and keep the missing-fact register in the manifest.",
            "lawyer-review": "Record responsible-lawyer approval for the exact current package version.",
            "client-transparency-notice": "Add a client-visible transparency notice covering risks, assumptions, and scope limits.",
            "export-formats": "Select supported export formats and lock export to the reviewed package version.",
            "version-notes": "Generate version notes for the current package version and make the summary available for delivery.",
        }
        return actions[section_id]

    def _overall_status(
        self,
        payload: dict[str, Any],
        sections: list[dict[str, Any]],
        risk_flags: list[dict[str, Any]],
    ) -> str:
        if not payload:
            return "template"
        if any(flag["severity"] == "blocking" for flag in risk_flags):
            return "blocked"
        if any(section["status"] == "fail" for section in sections):
            return "blocked"
        return "ready"

    def _count_status(self, sections: list[dict[str, Any]], status: str) -> int:
        return sum(1 for section in sections if section["status"] == status)

    def _documents(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        documents = _first_present(payload.get("documents"), payload.get("deliverables"), payload.get("artifacts"))
        if not isinstance(documents, list):
            return []
        return [item for item in documents if isinstance(item, dict)]

    def _document_count(self, payload: dict[str, Any]) -> int:
        return len(self._documents(payload))

    def _source_count(self, source: dict[str, Any]) -> int:
        numeric_values = [
            _safe_int(source.get("source_count"), 0),
            _safe_int(source.get("citation_count"), 0),
            _safe_int(source.get("support_count"), 0),
            _safe_int(source.get("supported_claim_count"), 0),
        ]
        list_values = [
            len(value)
            for value in (
                source.get("citations"),
                source.get("evidence_links"),
                source.get("source_anchors"),
                source.get("sources"),
            )
            if isinstance(value, list)
        ]
        return max([0, *numeric_values, *list_values])

    def _fact_item_resolved(self, item: dict[str, Any]) -> bool:
        status = _text(_first_present(item.get("status"), item.get("resolution_status"), item.get("decision"))).lower()
        if status:
            return status in RESOLVED_FACT_VALUES
        return _truthy(_first_present(item.get("resolved"), item.get("cleared"), item.get("waived")))

    def _current_version_id(self, payload: dict[str, Any]) -> Any:
        package = _first_section(payload, "package", "manifest", "delivery_package")
        artifact = _first_section(payload, "artifact")
        return _first_present(
            package.get("current_version_id"),
            package.get("version_id"),
            package.get("package_version_id"),
            artifact.get("current_version_id"),
            artifact.get("version_id"),
            payload.get("current_version_id"),
            payload.get("package_version_id"),
        )


def _first_section(payload: dict[str, Any], *names: str) -> dict[str, Any]:
    for name in names:
        section = payload.get(name)
        if isinstance(section, dict):
            return section
    return {}


def _first_present(*values: Any) -> Any:
    for value in values:
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


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "ok",
            "pass",
            "passed",
            "confirmed",
            "acknowledged",
            "approved",
            "complete",
            "completed",
        }
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _first_list_value(*values: Any) -> Any:
    for value in values:
        if isinstance(value, list):
            return value
    return None


def _formats(value: Any) -> list[str]:
    if isinstance(value, str):
        return [_text(value).lower()] if _text(value) else []
    if not isinstance(value, list):
        return []
    return _dedupe([_text(item).lower() for item in value if _text(item)])


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
