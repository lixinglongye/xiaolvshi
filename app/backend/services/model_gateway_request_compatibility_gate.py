from __future__ import annotations

import re
from typing import Any

from services.model_budget import COST_TIER_RANK, TASK_GROUPS, normalize_budget_task
from services.model_catalog import canonical_model_id, model_profile, task_default_model
from services.model_reasoning_policy import resolve_reasoning_effort
from services.model_request_policy import resolve_generation_request_policy


FORBIDDEN_REQUEST_FIELD_PATTERN = re.compile(
    r"(authorization|api[_-]?key|app_ai_key|headers|messages|prompt|raw_output|raw_response|"
    r"response_text|output_text|generated_text|candidate_text|document_text|legal_text|payload|email|phone)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization)",
    re.IGNORECASE,
)
HIGH_FREQUENCY_TASKS = {"cheap", "fast", "ocr", "classification"}
JSON_TASKS = {"cheap", "fast", "ocr", "classification", "review", "document-generation", "grounded-research", "agentic"}
MEDIA_ENDPOINT_TASKS = {"image", "video", "audio", "transcription"}


class ModelGatewayRequestCompatibilityGateService:
    """Build metadata-only request-shape evidence for OpenAI-compatible Gemini calls."""

    def build_gate(self, payload: Any = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        forbidden_payload_field_count = self._forbidden_field_count(data)
        task_inputs = self._task_inputs(data)
        rows = [self._task_row(item) for item in task_inputs]
        checks = self._checks(rows, forbidden_payload_field_count)
        blocking = [check for check in checks if check["status"] == "fail"]
        warnings = [check for check in checks if check["status"] == "warn"]
        status = "blocked" if blocking else ("review_required" if warnings else "ready")

        return {
            "id": "model-gateway-request-compatibility-gate",
            "title": "Model gateway request compatibility gate",
            "status": status,
            "method": {
                "type": "model-gateway-request-compatibility-gate",
                "notes": [
                    "Combines task default models, gateway model-name compatibility, request parameter policy, and Gemini reasoning policy into one request-shape review.",
                    "Checks that high-frequency cheap-first tasks stay on low-cost Gemini-compatible defaults with bounded temperature, max_tokens, and reasoning_effort.",
                    "Uses redacted placeholders for messages and response format only; it never sends requests or returns prompts, legal text, headers, payloads, model output, or credentials.",
                ],
            },
            "summary": {
                "task_count": len(rows),
                "ready_task_count": sum(1 for row in rows if row["compatibility_status"] == "ready"),
                "review_task_count": sum(1 for row in rows if row["compatibility_status"] == "review_required"),
                "blocked_task_count": sum(1 for row in rows if row["compatibility_status"] == "blocked"),
                "cheap_first_task_count": sum(1 for row in rows if row["cheap_first_task"]),
                "cheap_first_ready_count": sum(
                    1 for row in rows if row["cheap_first_task"] and row["compatibility_status"] == "ready"
                ),
                "gateway_prefixed_model_count": sum(1 for row in rows if row["gateway_prefixed_model"]),
                "unknown_model_count": sum(1 for row in rows if not row["known_catalog_model"]),
                "reasoning_omitted_count": sum(1 for row in rows if row["gateway_request_shape"]["reasoning_effort"] is None),
                "json_response_format_count": sum(
                    1 for row in rows if row["gateway_request_shape"]["response_format_mode"] == "json"
                ),
                "forbidden_payload_field_count": forbidden_payload_field_count,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "raw_payload_echoed": False,
                "credentials_included": False,
            },
            "task_rows": rows,
            "checks": checks,
            "blocking_check_ids": [check["id"] for check in blocking],
            "warning_check_ids": [check["id"] for check in warnings],
            "recommended_actions": self._recommended_actions(rows, forbidden_payload_field_count),
            "privacy_boundary": {
                "metadata_only": True,
                "configuration_written": False,
                "gateway_called": False,
                "network_called": False,
                "credentials_included": False,
                "headers_included": False,
                "request_body_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "raw_payload_echoed": False,
                "output_scope": "task ids, sanitized model ids, canonical model ids, cost tiers, parameter caps, reasoning policy decisions, and release actions only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "model_quality_claimed": False,
                "pricing_accuracy_claimed": False,
                "automatic_default_change_claimed": False,
                "production_compatibility_claimed": False,
            },
            "validation_commands": [
                "python -m pytest tests/test_model_gateway_request_compatibility_gate.py tests/test_model_request_policy.py tests/test_model_reasoning_policy.py -q",
                "python -m pytest tests/test_model_gateway_compatibility.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _task_inputs(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        supplied = data.get("tasks")
        if isinstance(supplied, list) and supplied:
            return [item if isinstance(item, dict) else {"task": item} for item in supplied[:40]]
        return [{"task": task} for task in TASK_GROUPS if task not in MEDIA_ENDPOINT_TASKS]

    def _task_row(self, item: dict[str, Any]) -> dict[str, Any]:
        task = normalize_budget_task(str(item.get("task") or "fast"))
        model = _safe_model_id(item.get("model")) or task_default_model(task)
        canonical = canonical_model_id(model)
        profile = model_profile(model)
        response_format = {"type": "json_object"} if task in JSON_TASKS else None
        if isinstance(item.get("response_format"), dict):
            response_format = item["response_format"]
        request_decision = resolve_generation_request_policy(
            task=task,
            requested_temperature=_safe_float(item.get("temperature")),
            requested_max_tokens=_safe_int(item.get("max_tokens")),
            response_format=response_format,
        )
        reasoning = resolve_reasoning_effort(
            model=canonical or model,
            task=task,
            requested_effort=_safe_text(item.get("reasoning_effort")) or None,
        )
        reason_codes = self._reason_codes(task, model, profile, request_decision, reasoning)
        status = self._row_status(reason_codes)
        return {
            "id": f"gateway-request-{task}",
            "task": task,
            "model": model,
            "canonical_model": canonical,
            "known_catalog_model": profile is not None,
            "gemini_like": _is_gemini_like(model, profile),
            "gateway_prefixed_model": bool(canonical and canonical != model.strip().lower()),
            "cost_tier": profile.cost_tier if profile else "unknown",
            "max_default_cost_tier": _max_default_cost_tier(task),
            "cheap_first_task": task in HIGH_FREQUENCY_TASKS,
            "compatibility_status": status,
            "release_action": self._release_action(status, task),
            "gateway_request_shape": {
                "messages": "redacted_placeholders_only",
                "response_format_mode": request_decision.response_format_mode,
                "temperature": request_decision.effective_temperature,
                "max_tokens": request_decision.effective_max_tokens,
                "reasoning_effort": reasoning.gateway_parameter,
                "request_body_returned": False,
                "headers_returned": False,
            },
            "request_policy": {
                "temperature_adjusted": request_decision.temperature_adjusted,
                "max_tokens_adjusted": request_decision.max_tokens_adjusted,
                "cost_mode": request_decision.cost_mode,
            },
            "reasoning_policy": {
                "effective_effort": reasoning.effective_effort,
                "gateway_parameter": reasoning.gateway_parameter,
                "cost_mode": reasoning.cost_mode,
                "adjusted": reasoning.adjusted,
            },
            "reason_codes": reason_codes,
            "next_action": self._next_action(status, reason_codes),
        }

    def _reason_codes(
        self,
        task: str,
        model: str,
        profile: Any,
        request_decision: Any,
        reasoning: Any,
    ) -> list[str]:
        codes: list[str] = []
        if not _is_gemini_like(model, profile):
            codes.append("non-gemini-default")
        if profile is None:
            codes.append("unknown-catalog-model")
        elif _tier_rank(profile.cost_tier) > _tier_rank(_max_default_cost_tier(task)):
            codes.append("model-cost-tier-over-task-bound")
        if task in HIGH_FREQUENCY_TASKS and request_decision.effective_temperature > 0.5:
            codes.append("high-frequency-temperature-too-high")
        if task in HIGH_FREQUENCY_TASKS and request_decision.effective_max_tokens > 4096:
            codes.append("high-frequency-token-cap-too-high")
        if task in HIGH_FREQUENCY_TASKS and reasoning.cost_mode == "elevated-thinking":
            codes.append("high-frequency-reasoning-too-expensive")
        if reasoning.gateway_parameter is None and _is_gemini_like(model, profile) and task != "pdf":
            codes.append("reasoning-parameter-omitted")
        if request_decision.response_format_mode == "json" and request_decision.effective_temperature > 0.2:
            codes.append("json-temperature-ceiling-missed")
        return _dedupe(codes) or ["gateway-request-compatible"]

    def _row_status(self, reason_codes: list[str]) -> str:
        blocking = {
            "non-gemini-default",
            "unknown-catalog-model",
            "model-cost-tier-over-task-bound",
            "high-frequency-temperature-too-high",
            "high-frequency-token-cap-too-high",
            "high-frequency-reasoning-too-expensive",
            "json-temperature-ceiling-missed",
        }
        if any(code in blocking for code in reason_codes):
            return "blocked"
        if "reasoning-parameter-omitted" in reason_codes:
            return "review_required"
        return "ready"

    def _checks(self, rows: list[dict[str, Any]], forbidden_payload_field_count: int) -> list[dict[str, str]]:
        blocked_rows = [row for row in rows if row["compatibility_status"] == "blocked"]
        review_rows = [row for row in rows if row["compatibility_status"] == "review_required"]
        cheap_first_rows = [row for row in rows if row["cheap_first_task"]]
        return [
            {
                "id": "sanitized-request-shape-only",
                "status": "fail" if forbidden_payload_field_count else "pass",
                "reason": "Input included forbidden raw request, header, prompt, payload, or credential fields."
                if forbidden_payload_field_count
                else "Gate output is limited to request-shape metadata and redacted placeholders.",
            },
            {
                "id": "cheap-first-gemini-compatible",
                "status": "pass"
                if cheap_first_rows and all(row["compatibility_status"] == "ready" for row in cheap_first_rows)
                else "fail",
                "reason": "High-frequency routes use Gemini-compatible low-cost defaults with bounded request parameters."
                if cheap_first_rows and all(row["compatibility_status"] == "ready" for row in cheap_first_rows)
                else "One or more high-frequency routes are not request-compatible for cheap-first Gemini defaults.",
            },
            {
                "id": "all-task-request-policy-covered",
                "status": "fail" if blocked_rows else ("warn" if review_rows else "pass"),
                "reason": f"{len(blocked_rows)} blocked task rows and {len(review_rows)} review rows require maintainer action."
                if blocked_rows or review_rows
                else "All task rows have compatible request policy and reasoning policy evidence.",
            },
            {
                "id": "no-gateway-or-config-write",
                "status": "pass",
                "reason": "The gate does not call gateways, send requests, write configuration, or shift traffic.",
            },
        ]

    def _recommended_actions(self, rows: list[dict[str, Any]], forbidden_payload_field_count: int) -> list[str]:
        if forbidden_payload_field_count:
            return [
                "Discard raw request payloads and resubmit task, model, temperature, max_tokens, response_format, and reasoning_effort metadata only.",
                "Do not use payloads with headers, prompts, legal text, credentials, or model output in ModelOps evidence.",
            ]
        blocked = [row for row in rows if row["compatibility_status"] == "blocked"]
        if blocked:
            return [
                "Keep blocked task/model pairs out of default routing until model catalog, request policy, and reasoning policy are aligned.",
                "Use cheap Gemini Flash-Lite defaults first for fast, OCR, and classification routes.",
            ]
        review = [row for row in rows if row["compatibility_status"] == "review_required"]
        if review:
            return [
                "Review rows with omitted reasoning parameters before promoting unknown gateway-specific Gemini names.",
                "Keep request bodies redacted and rerun validation before default changes.",
            ]
        return [
            "Gateway request shape is ready for cheap-first maintainer review without sending any live request.",
            "Keep high-frequency routes on bounded Flash-Lite style defaults unless quality gates require escalation.",
        ]

    def _next_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "Use this metadata-only request shape for maintainer review; do not send live probes from this gate."
        if status == "review_required":
            return "Review omitted or gateway-specific reasoning compatibility before default promotion."
        return f"Block default promotion until request compatibility issues are fixed: {', '.join(reason_codes[:5])}."

    def _release_action(self, status: str, task: str) -> str:
        if status == "ready":
            return "eligible_for_cheap_first_request_review"
        if status == "review_required":
            return "require_request_compatibility_review"
        if task in HIGH_FREQUENCY_TASKS:
            return "block_high_frequency_default_promotion"
        return "block_default_promotion_until_request_shape_is_safe"

    def _forbidden_field_count(self, value: Any) -> int:
        return min(20, len(self._forbidden_hits(value)))

    def _forbidden_hits(self, value: Any) -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if FORBIDDEN_REQUEST_FIELD_PATTERN.search(str(key)):
                    hits.append("forbidden-field")
                    continue
                hits.extend(self._forbidden_hits(child))
                if len(hits) >= 20:
                    return hits[:20]
        elif isinstance(value, list):
            for child in value[:50]:
                hits.extend(self._forbidden_hits(child))
                if len(hits) >= 20:
                    return hits[:20]
        elif isinstance(value, str) and SENSITIVE_VALUE_PATTERN.search(value[:4096]):
            hits.append("sensitive-value")
        return hits[:20]


def _max_default_cost_tier(task: str) -> str:
    if task in HIGH_FREQUENCY_TASKS:
        return "low"
    if task == "pdf":
        return "premium"
    return "medium"


def _tier_rank(cost_tier: str | None) -> int:
    return COST_TIER_RANK.get(cost_tier or "", 99)


def _safe_model_id(value: Any) -> str:
    text = _safe_text(value).lower()
    if not text:
        return ""
    return re.sub(r"[^a-z0-9_./:-]+", "-", text).strip("-")[:160]


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if SENSITIVE_VALUE_PATTERN.search(text):
        return ""
    return re.sub(r"[\r\n\t]+", " ", text)[:240]


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_gemini_like(model: str, profile: Any) -> bool:
    value = model.strip().lower()
    return bool(profile and getattr(profile, "family", "") == "gemini") or "gemini" in value


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
