from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


MAX_SOURCE_IDS = 64
SAFE_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:_.-]{0,127}$")
LIKELY_SENSITIVE_ID_RE = re.compile(r"^\d{7,}$|^\d{3,}[-_.]\d{3,}[-_.]?\d{0,}$")

CITED_SOURCE_ID_KEYS = {
    "answer_citation_source_id",
    "answer_citation_source_ids",
    "citation_source_id",
    "citation_source_ids",
    "cited_source_id",
    "cited_source_ids",
    "source_id",
    "source_ids",
}
SELECTED_SOURCE_ID_KEYS = (
    "legal_rag_selected_source_ids",
    "selected_source_ids",
)
STALE_SOURCE_ID_KEYS = (
    "stale_source_ids",
    "blocked_source_ids",
)
UNKNOWN_SOURCE_ID_KEYS = (
    "unknown_source_ids",
)
SKIPPED_CONTAINER_KEYS = {
    "coverage_counts",
    "filters",
    "metadata",
    "privacy_boundary",
    "repository_filters",
    "request_metadata",
    "retrieval_plan",
    "selected_sources",
}
PRIVACY_BOUNDARY = {
    "raw_legal_text_included": False,
    "user_claims_included": False,
    "pii_included": False,
    "output_scope": "sanitized source identifiers, status, counts, and reason codes only",
}


class LegalRagSelectedSourceValidationService:
    """Validate generated Legal RAG citations against request-selected sources."""

    def validate(
        self,
        *,
        request_metadata: Mapping[str, Any] | None,
        citation_map: Any | None = None,
        generation_plan: Any | None = None,
    ) -> dict[str, Any]:
        selected = _extract_selected_source_ids(request_metadata)
        cited = _extract_cited_source_ids(citation_map=citation_map, generation_plan=generation_plan)
        freshness = _extract_freshness_source_ids(request_metadata, generation_plan)

        selected_source_ids = selected["values"]
        cited_source_ids = cited["values"]
        selected_set = set(selected_source_ids)
        cited_set = set(cited_source_ids)

        unexpected_source_ids = [source_id for source_id in cited_source_ids if source_id not in selected_set]
        missing_selected_source_ids = [source_id for source_id in selected_source_ids if source_id not in cited_set]
        stale_source_ids = [
            source_id for source_id in cited_source_ids if source_id in freshness["stale_source_ids"]
        ]
        unknown_source_ids = _dedupe(
            [
                source_id
                for source_id in cited_source_ids
                if source_id in freshness["unknown_source_ids"] or source_id not in selected_set
            ]
        )

        reason_codes = _reason_codes(
            selected=selected,
            cited=cited,
            selected_source_ids=selected_source_ids,
            cited_source_ids=cited_source_ids,
            unexpected_source_ids=unexpected_source_ids,
            missing_selected_source_ids=missing_selected_source_ids,
            stale_source_ids=stale_source_ids,
            unknown_source_ids=unknown_source_ids,
        )
        blocking_reasons = {
            "missing_selected_source_context",
            "missing_citation_payload",
            "unexpected_cited_source_ids",
            "stale_cited_source_ids",
            "unknown_cited_source_ids",
            "missing_selected_source_citations",
        }
        status = "blocked" if blocking_reasons.intersection(reason_codes) else "pass"
        if status == "pass" and reason_codes:
            status = "pass_with_warnings"

        return {
            "status": status,
            "selected_source_ids": selected_source_ids,
            "cited_source_ids": cited_source_ids,
            "unexpected_source_ids": unexpected_source_ids,
            "missing_selected_source_ids": missing_selected_source_ids,
            "stale_source_ids": stale_source_ids,
            "unknown_source_ids": unknown_source_ids,
            "reason_codes": reason_codes,
            "counts": {
                "selected_source_count": len(selected_source_ids),
                "cited_source_count": len(cited_source_ids),
                "unexpected_source_count": len(unexpected_source_ids),
                "missing_selected_source_count": len(missing_selected_source_ids),
                "stale_source_count": len(stale_source_ids),
                "unknown_source_count": len(unknown_source_ids),
                "invalid_selected_source_id_count": selected["invalid_count"],
                "duplicate_selected_source_id_count": selected["duplicate_count"],
                "invalid_cited_source_id_count": cited["invalid_count"],
                "duplicate_cited_source_id_count": cited["duplicate_count"],
            },
            "privacy_boundary": dict(PRIVACY_BOUNDARY),
        }


def validate_selected_source_citations(
    *,
    request_metadata: Mapping[str, Any] | None,
    citation_map: Any | None = None,
    generation_plan: Any | None = None,
) -> dict[str, Any]:
    return LegalRagSelectedSourceValidationService().validate(
        request_metadata=request_metadata,
        citation_map=citation_map,
        generation_plan=generation_plan,
    )


def _extract_selected_source_ids(request_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    metadata = _record(request_metadata) or {}
    legal_rag = _record(metadata.get("legal_rag")) or {}
    groups = (
        metadata.get("legal_rag_selected_source_ids"),
        legal_rag.get("selected_source_ids"),
        metadata.get("selected_source_ids"),
    )
    empty_state = _empty_source_state()
    for group in groups:
        state = _safe_source_ids(_candidate_values(group))
        if state["values"]:
            return state
        if state["invalid_count"]:
            empty_state["invalid_count"] += state["invalid_count"]
    return empty_state


def _extract_cited_source_ids(*, citation_map: Any | None, generation_plan: Any | None) -> dict[str, Any]:
    state = _empty_source_state()
    _collect_cited_source_candidates(citation_map, state)
    _collect_cited_source_candidates(generation_plan, state)
    return state


def _collect_cited_source_candidates(value: Any, state: dict[str, Any], *, key_hint: str = "") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            safe_key = str(key or "").strip().lower()
            if safe_key in SKIPPED_CONTAINER_KEYS:
                continue
            if safe_key in CITED_SOURCE_ID_KEYS:
                _add_source_candidates(state, _candidate_values(item))
                continue
            _collect_cited_source_candidates(item, state, key_hint=safe_key)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_cited_source_candidates(item, state, key_hint=key_hint)
        return
    if key_hint in CITED_SOURCE_ID_KEYS:
        _add_source_candidates(state, _candidate_values(value))


def _extract_freshness_source_ids(
    request_metadata: Mapping[str, Any] | None,
    generation_plan: Any | None,
) -> dict[str, set[str]]:
    state = {"stale_source_ids": set(), "unknown_source_ids": set()}
    for payload in (request_metadata, generation_plan):
        _collect_freshness_candidates(payload, state)
    return state


def _collect_freshness_candidates(value: Any, state: dict[str, set[str]]) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            safe_key = str(key or "").strip().lower()
            if safe_key in STALE_SOURCE_ID_KEYS:
                state["stale_source_ids"].update(_safe_source_ids(_candidate_values(item))["values"])
                continue
            if safe_key in UNKNOWN_SOURCE_ID_KEYS:
                state["unknown_source_ids"].update(_safe_source_ids(_candidate_values(item))["values"])
                continue
            if safe_key == "selected_sources":
                _collect_selected_source_freshness(item, state)
                continue
            _collect_freshness_candidates(item, state)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            _collect_freshness_candidates(item, state)


def _collect_selected_source_freshness(value: Any, state: dict[str, set[str]]) -> None:
    if not isinstance(value, (list, tuple)):
        return
    for item in value:
        source = _record(item)
        if not source:
            continue
        source_id = _safe_source_ids(_candidate_values(source.get("source_id")))["values"]
        if not source_id:
            continue
        freshness_status = str(source.get("freshness_status") or "").strip().lower()
        if freshness_status == "stale":
            state["stale_source_ids"].add(source_id[0])
        elif freshness_status == "unknown":
            state["unknown_source_ids"].add(source_id[0])


def _candidate_values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        for key in ("source_id", "id"):
            if key in value:
                return _candidate_values(value.get(key))
        return []
    if isinstance(value, Iterable):
        values: list[Any] = []
        for item in value:
            if item is None:
                values.append(None)
            else:
                values.extend(_candidate_values(item))
        return values
    return [value]


def _empty_source_state() -> dict[str, Any]:
    return {"values": [], "invalid_count": 0, "duplicate_count": 0}


def _safe_source_ids(values: Iterable[Any]) -> dict[str, Any]:
    state = _empty_source_state()
    _add_source_candidates(state, values)
    return state


def _add_source_candidates(state: dict[str, Any], values: Iterable[Any]) -> None:
    seen = set(state["values"])
    for value in values:
        text = str(value or "").strip()
        if not _is_safe_source_id(text):
            state["invalid_count"] += 1
            continue
        if text in seen:
            state["duplicate_count"] += 1
            continue
        if len(state["values"]) >= MAX_SOURCE_IDS:
            break
        seen.add(text)
        state["values"].append(text)


def _reason_codes(
    *,
    selected: dict[str, Any],
    cited: dict[str, Any],
    selected_source_ids: list[str],
    cited_source_ids: list[str],
    unexpected_source_ids: list[str],
    missing_selected_source_ids: list[str],
    stale_source_ids: list[str],
    unknown_source_ids: list[str],
) -> list[str]:
    codes: list[str] = []
    if selected["invalid_count"]:
        codes.append("invalid_selected_source_ids_dropped")
    if selected["duplicate_count"]:
        codes.append("duplicate_selected_source_ids_dropped")
    if cited["invalid_count"]:
        codes.append("invalid_cited_source_ids_dropped")
    if cited["duplicate_count"]:
        codes.append("duplicate_cited_source_ids_dropped")
    if not selected_source_ids:
        codes.append("missing_selected_source_context")
    if selected_source_ids and not cited_source_ids:
        codes.append("missing_citation_payload")
    if unexpected_source_ids:
        codes.append("unexpected_cited_source_ids")
    if stale_source_ids:
        codes.append("stale_cited_source_ids")
    if unknown_source_ids:
        codes.append("unknown_cited_source_ids")
    if missing_selected_source_ids:
        codes.append("missing_selected_source_citations")
    return codes


def _record(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _is_safe_source_id(value: str) -> bool:
    if not SAFE_SOURCE_ID_RE.match(value):
        return False
    return not LIKELY_SENSITIVE_ID_RE.match(value)


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
