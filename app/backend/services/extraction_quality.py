from __future__ import annotations

from typing import Any


class ExtractionQualityAuditService:
    """Assess whether extracted text is good enough before model review."""

    def evaluate(self, extraction: dict[str, Any] | None = None) -> dict[str, Any]:
        extraction = extraction or {}
        char_count = _safe_int(extraction.get("char_count"), 0)
        page_count = _safe_int(extraction.get("page_count"), 0)
        low_text_pages = _list_int(extraction.get("low_text_pages"))
        ocr_pages = _list_int(extraction.get("ocr_pages"))
        text_layer_pages = _list_int(extraction.get("text_layer_pages"))
        warnings = [str(item) for item in extraction.get("warnings") or [] if str(item).strip()]
        density = round(char_count / page_count, 1) if page_count > 0 else None

        blocking = self._blocking_reasons(char_count=char_count, page_count=page_count, density=density)
        quality_warnings = self._warning_reasons(
            char_count=char_count,
            page_count=page_count,
            density=density,
            low_text_pages=low_text_pages,
            ocr_pages=ocr_pages,
            text_layer_pages=text_layer_pages,
            extraction_warnings=warnings,
        )
        status = "fail" if blocking else "warn" if quality_warnings else "pass"

        return {
            "status": status,
            "score": self._score(char_count, page_count, density, low_text_pages, ocr_pages, warnings, blocking),
            "char_count": char_count,
            "page_count": page_count or None,
            "chars_per_page": density,
            "text_layer_page_count": len(text_layer_pages),
            "low_text_page_count": len(low_text_pages),
            "ocr_page_count": len(ocr_pages),
            "blocking_reasons": blocking,
            "warning_reasons": quality_warnings,
            "recommended_actions": self._recommended_actions(blocking, quality_warnings),
        }

    def _blocking_reasons(self, *, char_count: int, page_count: int, density: float | None) -> list[str]:
        reasons: list[str] = []
        if char_count <= 0:
            reasons.append("No reviewable text was extracted.")
        elif char_count < 120:
            reasons.append("Extracted text is too short for reliable legal review.")
        if page_count >= 3 and density is not None and density < 30:
            reasons.append("Extracted text density is too low for a multi-page legal document.")
        return reasons

    def _warning_reasons(
        self,
        *,
        char_count: int,
        page_count: int,
        density: float | None,
        low_text_pages: list[int],
        ocr_pages: list[int],
        text_layer_pages: list[int],
        extraction_warnings: list[str],
    ) -> list[str]:
        reasons: list[str] = []
        if page_count and low_text_pages and len(low_text_pages) / page_count >= 0.25:
            reasons.append("A large share of pages had weak text layers.")
        if page_count and ocr_pages and len(ocr_pages) / page_count >= 0.25:
            reasons.append("OCR was required for a large share of pages.")
        if page_count and not text_layer_pages and ocr_pages:
            reasons.append("Document appears to be scanned; OCR output should be spot-checked.")
        if density is not None and 30 <= density < 120:
            reasons.append("Extracted text density is low; key clauses may be missing.")
        if char_count > 200_000:
            reasons.append("Extracted text is near the review truncation limit.")
        reasons.extend(extraction_warnings[:3])
        return _unique(reasons)

    def _score(
        self,
        char_count: int,
        page_count: int,
        density: float | None,
        low_text_pages: list[int],
        ocr_pages: list[int],
        warnings: list[str],
        blocking: list[str],
    ) -> int:
        score = 100
        if char_count < 500:
            score -= 25
        if density is not None and density < 120:
            score -= 20
        if page_count:
            score -= min(25, int(len(low_text_pages) / page_count * 35))
            score -= min(15, int(len(ocr_pages) / page_count * 20))
        score -= min(15, len(warnings) * 3)
        if blocking:
            score = min(score, 55)
        return max(0, min(100, score))

    def _recommended_actions(self, blocking: list[str], warnings: list[str]) -> list[str]:
        actions: list[str] = []
        if blocking:
            actions.append("Stop model review and ask for a clearer PDF, DOCX, or copyable text version.")
        if any("OCR" in item or "scanned" in item for item in warnings):
            actions.append("Spot-check OCR pages against the original file before relying on legal conclusions.")
        if any("density" in item for item in warnings + blocking):
            actions.append("Check whether tables, scanned images, or attachments were missed during extraction.")
        if not actions:
            actions.append("Extraction is suitable for staged deep review.")
        return actions


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _list_int(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    result: list[int] = []
    for item in value:
        try:
            result.append(int(item))
        except (TypeError, ValueError):
            continue
    return result


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
