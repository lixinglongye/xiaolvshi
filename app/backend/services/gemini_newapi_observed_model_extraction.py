from __future__ import annotations

import re
from typing import Any


EXTRACTOR_VERSION = "gemini-newapi-observed-model-extraction-v1"
MAX_OBSERVED_MODEL_CANDIDATES = 200
MAX_OBSERVED_MODEL_IDS = 40

SENSITIVE_MODEL_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|"
    r"\bbearer\s+[A-Za-z0-9._-]{10,}|password|secret|api[_-]?key|authorization|token)",
    re.IGNORECASE,
)

MODEL_ID_FIELD_KEYS = (
    "model",
    "model_id",
    "id",
    "name",
    "raw_model",
    "observed_model",
    "alias_model",
)
DIRECT_LIST_KEYS = ("observed_models", "model_ids", "gateway_models", "models")
RESPONSE_CONTAINER_KEYS = (
    "models_response",
    "gateway_models_response",
    "model_list",
    "modelList",
    "available_models",
    "availableModels",
    "response",
    "body",
    "result",
    "results",
)
NESTED_CONTAINER_KEYS = (
    "data",
    "models",
    "items",
    "result",
    "results",
    "available_models",
    "availableModels",
    "model_list",
    "modelList",
    "response",
    "body",
)
SIGNAL_KEYS = (
    "gateway_probe_evaluation",
    "observed_gemini_model_intake_queue",
    "gemini_variant_matrix",
    "gemini_newapi_alias_capability_coverage",
)
SIGNAL_ROW_KEYS = (
    "model_rows",
    "queue_items",
    "observed_model_reviews",
    "alias_rows",
    "coverage_rows",
    "candidate_patch_rows",
)


def extract_observed_model_ids(
    payload: Any = None,
    *,
    max_candidates: int = MAX_OBSERVED_MODEL_CANDIDATES,
    max_model_ids: int = MAX_OBSERVED_MODEL_IDS,
) -> dict[str, Any]:
    """Extract sanitized model ids from common Gemini/NewAPI model-list shapes."""

    candidates: list[Any] = []
    source_fields: list[str] = []
    _append_from_payload(candidates, source_fields, payload, max_candidates)

    observed: list[str] = []
    rejected_sensitive_count = 0
    for item in candidates[:max_candidates]:
        safe = safe_model_id(item)
        if not safe:
            rejected_sensitive_count += 1
            continue
        if safe in observed:
            continue
        observed.append(safe)
        if len(observed) >= max_model_ids:
            break

    source_fields = list(dict.fromkeys(source_fields))
    return {
        "observed_models": observed,
        "model_ids": observed,
        "summary": {
            "extractor_version": EXTRACTOR_VERSION,
            "candidate_count": len(candidates),
            "accepted_model_count": len(observed),
            "dropped_model_count": max(0, len(candidates) - len(observed)),
            "rejected_sensitive_count": rejected_sensitive_count,
            "source_fields": source_fields,
            "max_candidate_count": max_candidates,
            "max_accepted_model_count": max_model_ids,
            "raw_payload_echoed": False,
            "supported_model_fields": list(MODEL_ID_FIELD_KEYS),
        },
    }


def safe_model_id(value: Any) -> str:
    if isinstance(value, dict):
        for key in MODEL_ID_FIELD_KEYS:
            if isinstance(value.get(key), str):
                value = value[key]
                break
        else:
            return ""
    if isinstance(value, (list, tuple, set)):
        return ""
    raw = str(value or "").strip().lower()[:180]
    if not raw or SENSITIVE_MODEL_VALUE_PATTERN.search(raw):
        return ""
    return re.sub(r"[^a-z0-9_.:/@?#=-]+", "-", raw).strip("-")


def _append_from_payload(
    candidates: list[Any],
    source_fields: list[str],
    value: Any,
    max_candidates: int,
) -> None:
    if isinstance(value, list):
        _append_list(candidates, source_fields, "payload", value, max_candidates)
        return
    if not isinstance(value, dict):
        return

    for key in DIRECT_LIST_KEYS:
        _append_list(candidates, source_fields, key, value.get(key), max_candidates)
    for key in RESPONSE_CONTAINER_KEYS:
        _append_container(candidates, source_fields, key, value.get(key), max_candidates)
    _append_container(candidates, source_fields, "data", value.get("data"), max_candidates)
    for key in SIGNAL_KEYS:
        _append_signal(candidates, source_fields, key, value.get(key), max_candidates)


def _append_signal(
    candidates: list[Any],
    source_fields: list[str],
    source: str,
    value: Any,
    max_candidates: int,
) -> None:
    if not isinstance(value, dict):
        return
    for key in SIGNAL_ROW_KEYS:
        _append_list(candidates, source_fields, f"{source}.{key}", value.get(key), max_candidates)


def _append_container(
    candidates: list[Any],
    source_fields: list[str],
    source: str,
    value: Any,
    max_candidates: int,
) -> None:
    if len(candidates) >= max_candidates:
        return
    if isinstance(value, list):
        _append_list(candidates, source_fields, source, value, max_candidates)
        return
    if not isinstance(value, dict):
        return
    if safe_model_id(value):
        _append_list(candidates, source_fields, source, [value], max_candidates)
        return
    for key in NESTED_CONTAINER_KEYS:
        child = value.get(key)
        if child is None:
            continue
        _append_container(candidates, source_fields, f"{source}.{key}", child, max_candidates)


def _append_list(
    candidates: list[Any],
    source_fields: list[str],
    source: str,
    value: Any,
    max_candidates: int,
) -> None:
    if not isinstance(value, list) or len(candidates) >= max_candidates:
        return
    remaining = max_candidates - len(candidates)
    candidates.extend(value[:remaining])
    source_fields.append(source)
