from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal


ImportStatus = Literal[
    "uploaded",
    "preflight",
    "ocr_needed",
    "ocr_failed",
    "parsed",
    "blocked",
    "manual_review",
]

IMPORT_STATUSES: tuple[ImportStatus, ...] = (
    "uploaded",
    "preflight",
    "ocr_needed",
    "ocr_failed",
    "parsed",
    "blocked",
    "manual_review",
)


@dataclass(frozen=True)
class ImportStatusDefinition:
    status: ImportStatus
    meaning: str
    next_action: str
    terminal: bool = False

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    retryable_statuses: tuple[str, ...]
    backoff_seconds: tuple[int, ...]
    blocked_after_attempts: int
    manual_review_after_attempts: int

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["retryable_statuses"] = list(self.retryable_statuses)
        data["backoff_seconds"] = list(self.backoff_seconds)
        return data


class OcrImportReadinessPolicyService:
    """Evaluate document import readiness for scanned or low-text legal files."""

    LOW_TEXT_PAGE_THRESHOLD = 80
    LOW_TEXT_PAGE_RATIO_THRESHOLD = 0.35
    DEFAULT_MAX_OCR_ATTEMPTS = 3

    def build_policy(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        retry_policy = self._retry_policy()
        detection = self._detect_scanned_or_low_text(payload)
        retry_state = self._retry_state(payload, retry_policy)
        blockers = self._blocking_conditions(payload, detection, retry_state)
        manual_review_conditions = self._manual_review_conditions(payload, detection, retry_state)
        status = self._status(payload, detection, retry_state, blockers, manual_review_conditions)

        return {
            "status": status,
            "policy_id": "ocr-import-readiness-policy-v1",
            "method": {
                "type": "deterministic-import-readiness-policy",
                "notes": [
                    "The policy evaluates metadata only; it does not store raw document text or images.",
                    "Routers can call build_policy(payload) after upload preflight and before parsing.",
                    "Scanning and OCR ambiguity should remain visible to reviewers instead of silently falling through to parsed.",
                ],
            },
            "status_enumeration": [item.to_api() for item in self._status_definitions()],
            "summary": {
                "ready_for_parse": status == "parsed",
                "ocr_required": detection["ocr_needed"],
                "blocked": status == "blocked",
                "manual_review_required": status == "manual_review",
                "low_text_page_count": detection["low_text_page_count"],
                "scanned_page_count": detection["scanned_page_count"],
                "ocr_attempt_count": retry_state["attempt_count"],
            },
            "scanned_or_low_text_detection": detection,
            "retry_policy": retry_policy.to_api(),
            "retry_state": retry_state,
            "blocking_conditions": blockers,
            "manual_review_conditions": manual_review_conditions,
            "recommended_next_actions": self._recommended_next_actions(status),
            "audit_record_requirements": [
                "document_id",
                "import_status",
                "page_count",
                "low_text_page_count",
                "scanned_page_count",
                "ocr_attempt_count",
                "ocr_engine_version",
                "reviewer_decision",
                "timestamp",
            ],
            "low_resource_validation_commands": [
                {
                    "id": "ocr-import-readiness-policy-tests",
                    "command": "python -m pytest tests/test_ocr_import_readiness_policy.py -q",
                    "resource_note": "Runs deterministic metadata tests only; no OCR engine, network call, or large document fixture is required.",
                },
                {
                    "id": "ocr-policy-secret-scan",
                    "command": "rg -n \"sk-[A-Za-z0-9]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}|(?i)(pwd|pass\\\\s*word|token)\\\\s*[:=]\" app/backend/services/ocr_import_readiness_policy.py app/backend/tests/test_ocr_import_readiness_policy.py docs/OCR_IMPORT_READINESS_POLICY.md",
                    "resource_note": "Expected result is no matches.",
                },
            ],
            "privacy_notes": [
                "Store document IDs, page-level counts, status labels, and OCR engine metadata instead of raw client text.",
                "Do not place uploaded images, extracted text, credentials, user contact details, or full file paths in readiness payloads.",
                "When manual review is required, show the reviewer sampled page numbers and detection reasons, not unnecessary personal data.",
            ],
            "future_api": {
                "suggested_endpoint": "POST /api/v1/imports/ocr-readiness",
                "integration_note": "Call after file upload preflight; use the returned status to decide whether to OCR, retry, block, or send to manual review.",
            },
        }

    def _status_definitions(self) -> tuple[ImportStatusDefinition, ...]:
        return (
            ImportStatusDefinition(
                status="uploaded",
                meaning="The file was received but has not passed import preflight checks.",
                next_action="Run MIME, size, page-count, encryption, and text-density checks.",
            ),
            ImportStatusDefinition(
                status="preflight",
                meaning="The file is being checked for structure, extractable text, and OCR needs.",
                next_action="Classify pages as text-readable, scanned, low-text, encrypted, or corrupted.",
            ),
            ImportStatusDefinition(
                status="ocr_needed",
                meaning="One or more pages appear scanned or have too little extractable text for reliable parsing.",
                next_action="Queue OCR before legal parsing or summarization.",
            ),
            ImportStatusDefinition(
                status="ocr_failed",
                meaning="The latest OCR attempt failed but retry budget may still remain.",
                next_action="Retry with backoff when failure reason is transient or engine-specific.",
            ),
            ImportStatusDefinition(
                status="parsed",
                meaning="The document has enough text or completed OCR output for downstream legal parsing.",
                next_action="Proceed to clause extraction, timeline building, or legal review workflows.",
                terminal=True,
            ),
            ImportStatusDefinition(
                status="blocked",
                meaning="The import should not continue automatically because blocking conditions are present.",
                next_action="Show the blocking reason and require user correction or support intervention.",
                terminal=True,
            ),
            ImportStatusDefinition(
                status="manual_review",
                meaning="The system cannot confidently decide OCR or parse readiness without human review.",
                next_action="Ask a reviewer to inspect page samples, OCR quality, and failure reasons.",
            ),
        )

    def _retry_policy(self) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=self.DEFAULT_MAX_OCR_ATTEMPTS,
            retryable_statuses=("ocr_needed", "ocr_failed"),
            backoff_seconds=(30, 120, 600),
            blocked_after_attempts=self.DEFAULT_MAX_OCR_ATTEMPTS,
            manual_review_after_attempts=2,
        )

    def _detect_scanned_or_low_text(self, payload: dict[str, Any]) -> dict[str, Any]:
        pages = payload.get("pages")
        page_metrics = pages if isinstance(pages, list) else []
        page_count = self._positive_int(payload.get("page_count")) or len(page_metrics)

        low_text_pages: list[int] = []
        scanned_pages: list[int] = []
        unreadable_pages: list[int] = []

        for index, page in enumerate(page_metrics, start=1):
            if not isinstance(page, dict):
                continue
            page_number = self._positive_int(page.get("page_number")) or index
            char_count = self._non_negative_int(page.get("text_char_count"))
            has_text_layer = page.get("has_text_layer")
            image_only = page.get("image_only")

            if char_count is not None and char_count < self.LOW_TEXT_PAGE_THRESHOLD:
                low_text_pages.append(page_number)
            if image_only is True or has_text_layer is False:
                scanned_pages.append(page_number)
            if page.get("corrupted") is True or page.get("readable") is False:
                unreadable_pages.append(page_number)

        explicit_scanned = payload.get("scan_detected") is True or payload.get("image_only") is True
        explicit_low_text = payload.get("low_text_detected") is True
        low_text_ratio = (len(low_text_pages) / page_count) if page_count else 0.0
        ocr_needed = (
            explicit_scanned
            or explicit_low_text
            or bool(scanned_pages)
            or bool(low_text_pages)
            or low_text_ratio >= self.LOW_TEXT_PAGE_RATIO_THRESHOLD
        )

        return {
            "ocr_needed": ocr_needed,
            "signals": {
                "explicit_scan_detected": explicit_scanned,
                "explicit_low_text_detected": explicit_low_text,
                "low_text_threshold_chars": self.LOW_TEXT_PAGE_THRESHOLD,
                "low_text_ratio_threshold": self.LOW_TEXT_PAGE_RATIO_THRESHOLD,
            },
            "page_count": page_count,
            "low_text_page_count": len(low_text_pages),
            "scanned_page_count": len(scanned_pages) + (1 if explicit_scanned and not scanned_pages else 0),
            "unreadable_page_count": len(unreadable_pages),
            "low_text_pages": low_text_pages,
            "scanned_pages": scanned_pages,
            "unreadable_pages": unreadable_pages,
        }

    def _retry_state(self, payload: dict[str, Any], retry_policy: RetryPolicy) -> dict[str, Any]:
        attempt_count = self._non_negative_int(payload.get("ocr_attempt_count")) or 0
        last_error = payload.get("ocr_last_error")
        retry_budget_remaining = max(retry_policy.max_attempts - attempt_count, 0)
        return {
            "attempt_count": attempt_count,
            "retry_budget_remaining": retry_budget_remaining,
            "latest_failure_reason": str(last_error) if last_error else None,
            "retry_allowed": retry_budget_remaining > 0,
            "blocked_by_retry_budget": attempt_count >= retry_policy.blocked_after_attempts,
            "manual_review_recommended": attempt_count >= retry_policy.manual_review_after_attempts,
        }

    def _blocking_conditions(
        self,
        payload: dict[str, Any],
        detection: dict[str, Any],
        retry_state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []

        if payload.get("encrypted") is True:
            blockers.append(
                {
                    "id": "encrypted-file",
                    "title": "Encrypted files cannot be imported automatically",
                    "reviewer_action": "Ask the user to upload an unlocked copy or handle unlock credentials outside the readiness payload.",
                }
            )
        if payload.get("unsupported_file_type") is True:
            blockers.append(
                {
                    "id": "unsupported-file-type",
                    "title": "The uploaded file type is not supported",
                    "reviewer_action": "Convert the document to a supported PDF or image format before OCR.",
                }
            )
        if payload.get("file_too_large") is True:
            blockers.append(
                {
                    "id": "file-too-large",
                    "title": "The uploaded file exceeds import limits",
                    "reviewer_action": "Split the file or use an approved large-file intake path.",
                }
            )
        if detection["unreadable_page_count"] > 0:
            blockers.append(
                {
                    "id": "unreadable-pages",
                    "title": "One or more pages cannot be read by preflight",
                    "reviewer_action": "Inspect the listed pages and request a clearer copy when needed.",
                }
            )
        if retry_state["blocked_by_retry_budget"]:
            blockers.append(
                {
                    "id": "ocr-retry-budget-exhausted",
                    "title": "OCR retry budget is exhausted",
                    "reviewer_action": "Block automatic retry and route the import to support or manual review.",
                }
            )

        return blockers

    def _manual_review_conditions(
        self,
        payload: dict[str, Any],
        detection: dict[str, Any],
        retry_state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        conditions: list[dict[str, Any]] = []

        if payload.get("mixed_orientation_detected") is True:
            conditions.append(
                {
                    "id": "mixed-page-orientation",
                    "title": "Mixed orientation may reduce OCR accuracy",
                    "reviewer_action": "Inspect rotated pages before relying on extraction.",
                }
            )
        if payload.get("handwriting_detected") is True:
            conditions.append(
                {
                    "id": "handwriting-detected",
                    "title": "Handwritten content needs reviewer confirmation",
                    "reviewer_action": "Confirm OCR quality or transcribe key handwritten sections.",
                }
            )
        if detection["ocr_needed"] and retry_state["manual_review_recommended"]:
            conditions.append(
                {
                    "id": "repeat-ocr-failure-risk",
                    "title": "Repeated OCR attempts indicate quality risk",
                    "reviewer_action": "Review page samples before another automatic retry.",
                }
            )
        if conditions and detection["page_count"] and detection["low_text_page_count"] == detection["page_count"]:
            conditions.append(
                {
                    "id": "all-pages-low-text",
                    "title": "All pages have low extractable text",
                    "reviewer_action": "Confirm the upload is a scanned document rather than a corrupted text layer.",
                }
            )

        return conditions

    def _status(
        self,
        payload: dict[str, Any],
        detection: dict[str, Any],
        retry_state: dict[str, Any],
        blockers: list[dict[str, Any]],
        manual_review_conditions: list[dict[str, Any]],
    ) -> ImportStatus:
        if not payload:
            return "uploaded"
        if blockers:
            return "blocked"
        if payload.get("ocr_status") == "failed":
            return "ocr_failed"
        if manual_review_conditions:
            return "manual_review"
        if detection["ocr_needed"]:
            return "ocr_needed"
        if payload.get("preflight_complete") is True or retry_state["attempt_count"] > 0:
            return "parsed"
        return "preflight"

    def _recommended_next_actions(self, status: ImportStatus) -> list[str]:
        actions = {
            "uploaded": [
                "Run upload preflight and page-level text-density checks.",
                "Keep downstream legal parsing disabled until readiness status changes.",
            ],
            "preflight": [
                "Finish text-layer, page readability, and file support checks.",
                "Emit ocr_needed when scanned or low-text signals appear.",
            ],
            "ocr_needed": [
                "Queue OCR using the configured engine and record attempt metadata.",
                "Show users that parsing is waiting on OCR rather than silently failing.",
            ],
            "ocr_failed": [
                "Retry with configured backoff while retry budget remains.",
                "Preserve the latest failure reason for reviewer inspection.",
            ],
            "parsed": [
                "Proceed to downstream legal parsing.",
                "Store import status and detection counts in the audit trail.",
            ],
            "blocked": [
                "Stop automatic import and show blocking condition IDs.",
                "Require a corrected upload, support action, or reviewer decision.",
            ],
            "manual_review": [
                "Route the document to a reviewer with page samples and detection reasons.",
                "Resume OCR or parsing only after the reviewer records a decision.",
            ],
        }
        return actions[status]

    def _positive_int(self, value: Any) -> int | None:
        parsed = self._non_negative_int(value)
        if parsed and parsed > 0:
            return parsed
        return None

    def _non_negative_int(self, value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None
