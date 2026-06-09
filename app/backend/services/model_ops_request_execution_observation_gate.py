from __future__ import annotations

import re
from typing import Any

from services.model_catalog import canonical_model_id
from services.model_ops_request_execution_preflight import ModelOpsRequestExecutionPreflightService


SAFE_OBSERVATION_FIELD_PATTERN = re.compile(
    r"(authorization|api[_-]?key|app_ai_key|headers|messages|prompt|payload|request_body|"
    r"response_body|raw_output|model_output|generated_text|candidate_text|document_text|"
    r"legal_text|email|phone|identity|password|secret|gateway_response)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization)",
    re.IGNORECASE,
)
HIGH_FREQUENCY_TASKS = {"fast", "ocr", "classification", "embedding"}


class ModelOpsRequestExecutionObservationGateService:
    """Compare sanitized post-run request metadata with cheap-first preflight rows."""

    def __init__(
        self,
        *,
        preflight_service: ModelOpsRequestExecutionPreflightService | None = None,
    ) -> None:
        self.preflight_service = preflight_service or ModelOpsRequestExecutionPreflightService()

    def build_gate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        forbidden_field_count = self._forbidden_field_count(data)
        preflight = self.preflight_service.build_preflight(data.get("preflight") if isinstance(data.get("preflight"), dict) else None)
        preflight_rows = {str(row.get("request_id")): row for row in preflight.get("request_rows", [])}
        observations = self._observations(data)
        rows = [self._row(index, observation, preflight_rows) for index, observation in enumerate(observations, start=1)]
        checks = self._checks(rows, forbidden_field_count, preflight)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]

        return {
            "id": "modelops-request-execution-observation-gate",
            "title": "ModelOps request execution observation gate",
            "status": "blocked" if blocking else ("review_required" if warnings else "ready"),
            "method": {
                "type": "metadata-only-request-execution-observation-gate",
                "notes": [
                    "Reviews sanitized post-run request metadata against request execution preflight rows.",
                    "Checks cheap-first alignment, local downgrade follow-through, observed cost, latency, fallback use, and error categories.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
            },
            "summary": {
                "observation_count": len(rows),
                "ready_observation_count": sum(1 for row in rows if row["observation_status"] == "ready"),
                "review_observation_count": sum(1 for row in rows if row["observation_status"] == "review_required"),
                "blocked_observation_count": sum(1 for row in rows if row["observation_status"] == "blocked"),
                "matched_preflight_count": sum(1 for row in rows if row["preflight_match"]),
                "high_frequency_observation_count": sum(1 for row in rows if row["high_frequency_task"]),
                "cheap_first_observed_count": sum(
                    1 for row in rows if row["high_frequency_task"] and row["cheap_first_observed"]
                ),
                "local_downgrade_followed_count": sum(1 for row in rows if row["local_downgrade_followed"]),
                "fallback_used_count": sum(1 for row in rows if row["fallback_used"]),
                "observed_cost_usd_sum": round(sum(row["observed_cost_usd"] or 0.0 for row in rows), 8),
                "forbidden_payload_field_count": forbidden_field_count,
                "raw_payload_echoed": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "credentials_included": False,
            },
            "observation_rows": rows,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "observation_policy": {
                "source_policy": "Observations must be externally supplied sanitized metadata from a reviewed run; this gate never executes the request.",
                "preflight_policy": "Every observed request should match a request_execution_preflight row before it is used as release evidence.",
                "cheap_first_policy": "High-frequency observations must keep the preflight resolved cheap-first model unless a reviewed local downgrade or block is recorded.",
                "cost_policy": "Observed cost must stay within the preflight request limit and task cost bounds.",
                "error_policy": "Provider/gateway errors are recorded as coarse categories only; raw responses and stack traces are rejected.",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "request_body_included": False,
                "headers_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "gateway_response_included": False,
                "credentials_included": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "output_scope": "request ids, task labels, sanitized model ids, status categories, token/cost/latency metadata, fallback flags, reason codes, and release actions only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "model_quality_claimed": False,
                "pricing_accuracy_claimed": False,
                "raw_run_replay_claimed": False,
                "automatic_default_change_claimed": False,
                "request_sent_by_gate": False,
            },
            "recommended_actions": self._recommended_actions(rows, forbidden_field_count),
            "source_preflight": {
                "id": preflight.get("id"),
                "status": preflight.get("status"),
                "request_count": preflight.get("summary", {}).get("request_count"),
                "blocking_check_ids": list(preflight.get("blocking_check_ids", []))[:12],
            },
            "validation_commands": [
                "python -m pytest tests/test_model_ops_request_execution_observation_gate.py tests/test_model_ops_request_execution_preflight.py -q",
                "python -m pytest tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _observations(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        supplied = data.get("observations")
        if isinstance(supplied, list) and supplied:
            return [item if isinstance(item, dict) else {"request_id": item} for item in supplied[:40]]
        return [
            {
                "request_id": "fast-default",
                "task": "fast",
                "resolved_model": "gemini-2.5-flash-lite",
                "status": "success",
                "observed_input_tokens": 1180,
                "observed_output_tokens": 220,
                "observed_cost_usd": 0.0002,
                "latency_ms": 900,
            },
            {
                "request_id": "classification-default",
                "task": "classification",
                "resolved_model": "gemini-2.5-flash-lite",
                "status": "success",
                "observed_input_tokens": 1520,
                "observed_output_tokens": 160,
                "observed_cost_usd": 0.00019,
                "latency_ms": 820,
            },
            {
                "request_id": "embedding-default",
                "task": "embedding",
                "resolved_model": "gemini-embedding-001",
                "status": "success",
                "observed_input_tokens": 24000,
                "observed_output_tokens": 0,
                "observed_cost_usd": 0.0036,
                "latency_ms": 1100,
            },
        ]

    def _row(self, index: int, observation: dict[str, Any], preflight_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
        request_id = _safe_text(observation.get("request_id")) or f"request-{index}"
        preflight = preflight_rows.get(request_id)
        task = _safe_text(observation.get("task")) or str(preflight.get("task") if preflight else "fast")
        task = task[:80]
        observed_model = _safe_model_id(observation.get("resolved_model") or observation.get("model"))
        if not observed_model and preflight:
            observed_model = str(preflight.get("resolved_model") or "")
        observed_status = _safe_status(observation.get("status"))
        observed_cost = _safe_float(_first_present(observation, "observed_cost_usd", "cost_usd"))
        observed_input_tokens = _safe_int(_first_present(observation, "observed_input_tokens", "input_tokens"))
        observed_output_tokens = _safe_int(_first_present(observation, "observed_output_tokens", "output_tokens"))
        latency_ms = _safe_int(observation.get("latency_ms"))
        fallback_used = observation.get("fallback_used") is True
        error_category = _safe_error_category(observation.get("error_category"))
        reason_codes = self._reason_codes(
            request_id=request_id,
            task=task,
            observed_model=observed_model,
            observed_status=observed_status,
            observed_cost=observed_cost,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            error_category=error_category,
            preflight=preflight,
        )
        observation_status = self._observation_status(reason_codes)
        return {
            "id": f"request-execution-observation-{_slug(request_id)}",
            "request_id": request_id,
            "task": task,
            "preflight_match": preflight is not None,
            "preflight_status": preflight.get("execution_status") if preflight else "missing",
            "preflight_resolved_model": preflight.get("resolved_model") if preflight else None,
            "observed_model": observed_model,
            "canonical_observed_model": canonical_model_id(observed_model),
            "observed_status": observed_status,
            "observed_input_tokens": observed_input_tokens,
            "observed_output_tokens": observed_output_tokens,
            "observed_total_tokens": (observed_input_tokens or 0) + (observed_output_tokens or 0),
            "observed_cost_usd": observed_cost,
            "preflight_cost_limit_usd": preflight.get("request_cost_limit_usd") if preflight else None,
            "latency_ms": latency_ms,
            "fallback_used": fallback_used,
            "error_category": error_category,
            "high_frequency_task": task in HIGH_FREQUENCY_TASKS,
            "cheap_first_observed": self._cheap_first_observed(task, observed_model),
            "local_downgrade_followed": bool(
                preflight
                and preflight.get("routed_to_recommended_model")
                and observed_model == preflight.get("resolved_model")
            ),
            "observation_status": observation_status,
            "release_action": self._release_action(observation_status, reason_codes),
            "reason_codes": reason_codes,
            "next_action": self._next_action(observation_status, reason_codes),
        }

    def _reason_codes(
        self,
        *,
        request_id: str,
        task: str,
        observed_model: str,
        observed_status: str,
        observed_cost: float | None,
        latency_ms: int | None,
        fallback_used: bool,
        error_category: str,
        preflight: dict[str, Any] | None,
    ) -> list[str]:
        codes: list[str] = []
        if preflight is None:
            codes.append("missing_preflight_row")
        elif preflight.get("execution_status") == "blocked":
            codes.append("observed_blocked_preflight_row")
        if observed_status not in {"success", "cached", "dry_run"}:
            codes.append("observed_request_not_successful")
        if task in HIGH_FREQUENCY_TASKS and not self._cheap_first_observed(task, observed_model):
            codes.append("high_frequency_observed_non_cheap_model")
        if preflight and observed_model != preflight.get("resolved_model"):
            if fallback_used:
                codes.append("fallback_model_used")
            else:
                codes.append("observed_model_mismatch")
        if observed_cost is None:
            codes.append("observed_cost_missing")
        elif preflight and preflight.get("request_cost_limit_usd") is not None and observed_cost > float(preflight["request_cost_limit_usd"]):
            codes.append("observed_cost_over_preflight_limit")
        if latency_ms is None:
            codes.append("latency_missing")
        elif latency_ms > self._latency_limit_ms(task):
            codes.append("latency_over_review_limit")
        if error_category and error_category not in {"none", "cached", "rate_limited", "timeout", "provider_5xx", "client_4xx"}:
            codes.append("unknown_error_category")
        return _dedupe(codes) or ["request_execution_observation_ready"]

    def _checks(
        self,
        rows: list[dict[str, Any]],
        forbidden_field_count: int,
        preflight: dict[str, Any],
    ) -> list[dict[str, Any]]:
        blocked = [row["id"] for row in rows if row["observation_status"] == "blocked"]
        review = [row["id"] for row in rows if row["observation_status"] == "review_required"]
        missing_preflight = [row["id"] for row in rows if not row["preflight_match"]]
        cheap_first_gaps = [
            row["id"] for row in rows if row["high_frequency_task"] and not row["cheap_first_observed"]
        ]
        cost_gaps = [
            row["id"] for row in rows if "observed_cost_missing" in row["reason_codes"]
            or "observed_cost_over_preflight_limit" in row["reason_codes"]
        ]
        return [
            _check(
                "sanitized-observation-metadata-only",
                "fail" if forbidden_field_count else "pass",
                "Input contains no raw prompt, message, header, payload, legal text, model output, gateway response, credential, email, or identity fields.",
                [str(forbidden_field_count)],
            ),
            _check(
                "source-preflight-ready",
                "fail" if preflight.get("status") == "blocked" else ("warn" if preflight.get("status") == "review_required" else "pass"),
                "Observation review starts from request execution preflight evidence.",
                list(preflight.get("blocking_check_ids", []))[:12],
            ),
            _check(
                "observations-match-preflight",
                "fail" if missing_preflight else "pass",
                "Every observation maps to a sanitized preflight request id.",
                missing_preflight,
            ),
            _check(
                "observed-cheap-first-alignment",
                "fail" if cheap_first_gaps else "pass",
                "High-frequency observed requests use cheap-first Gemini models.",
                cheap_first_gaps,
            ),
            _check(
                "observed-cost-within-preflight-limit",
                "fail" if cost_gaps else "pass",
                "Observed cost metadata is present and stays within the preflight request limit.",
                cost_gaps,
            ),
            _check(
                "observation-review-exceptions-visible",
                "warn" if review else "pass",
                "Fallback, latency, or coarse error observations are visible for maintainer review.",
                review,
            ),
            _check(
                "no-provider-side-effects",
                "pass",
                "The observation gate does not execute model calls, gateway calls, network calls, traffic shifts, or configuration writes.",
                [],
            ),
            _check(
                "all-observation-rows-ready",
                "fail" if blocked else ("warn" if review else "pass"),
                "Every observation row has a release action before it is used as release evidence.",
                blocked + review,
            ),
        ]

    def _observation_status(self, reason_codes: list[str]) -> str:
        blocking = {
            "missing_preflight_row",
            "observed_blocked_preflight_row",
            "observed_request_not_successful",
            "high_frequency_observed_non_cheap_model",
            "observed_model_mismatch",
            "observed_cost_missing",
            "observed_cost_over_preflight_limit",
            "unknown_error_category",
        }
        if any(code in blocking for code in reason_codes):
            return "blocked"
        review = {"fallback_model_used", "latency_missing", "latency_over_review_limit"}
        if any(code in review for code in reason_codes):
            return "review_required"
        return "ready"

    def _recommended_actions(self, rows: list[dict[str, Any]], forbidden_field_count: int) -> list[str]:
        if forbidden_field_count:
            return [
                "Discard raw run payloads and resubmit only request_id, task, resolved_model, status, tokens, cost, latency, fallback_used, and error_category metadata.",
                "Do not include headers, prompts, legal text, gateway responses, model output, emails, identifiers, or credentials in observation evidence.",
            ]
        blocked = [row for row in rows if row["observation_status"] == "blocked"]
        if blocked:
            return [
                "Do not use blocked observations as release evidence until they match a ready preflight row and pass cheap-first/cost checks.",
                "Keep high-frequency observations on Flash-Lite or Gemini embedding defaults before expanding traffic.",
            ]
        review = [row for row in rows if row["observation_status"] == "review_required"]
        if review:
            return [
                "Review fallback, latency, and coarse error observations before promoting request execution evidence.",
                "Attach the matching preflight output and maintainer notes to the release packet.",
            ]
        return [
            "Request execution observations are ready as metadata-only evidence.",
            "Continue collecting only token, cost, latency, fallback, and status metadata; never archive raw prompts or model outputs.",
        ]

    def _cheap_first_observed(self, task: str, model: str) -> bool:
        canonical = canonical_model_id(model) or model
        if task == "embedding":
            return "embedding" in canonical
        if task in {"fast", "ocr", "classification"}:
            return "flash-lite" in canonical
        return True

    def _latency_limit_ms(self, task: str) -> int:
        if task in {"fast", "classification"}:
            return 5_000
        if task == "embedding":
            return 10_000
        if task in {"ocr", "agentic", "review", "grounded-research"}:
            return 30_000
        return 60_000

    def _forbidden_field_count(self, value: Any) -> int:
        return min(20, len(self._forbidden_hits(value)))

    def _forbidden_hits(self, value: Any) -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if SAFE_OBSERVATION_FIELD_PATTERN.search(str(key)):
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

    def _release_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "accept_observation_as_release_evidence"
        if status == "review_required":
            return "require_maintainer_review_before_release_evidence"
        if "high_frequency_observed_non_cheap_model" in reason_codes:
            return "block_observation_until_cheap_first_model_is_used"
        if "observed_cost_over_preflight_limit" in reason_codes or "observed_cost_missing" in reason_codes:
            return "block_observation_until_cost_metadata_is_safe"
        return "block_observation_until_preflight_alignment_passes"

    def _next_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "Keep this metadata-only observation linked to its request execution preflight row."
        if status == "review_required":
            return "Review fallback, latency, or coarse error metadata before using this observation for release evidence."
        return f"Do not use this observation as release evidence until issues are fixed: {', '.join(reason_codes[:6])}."


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if SENSITIVE_VALUE_PATTERN.search(text):
        return ""
    return re.sub(r"[\r\n\t]+", " ", text)[:180]


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _safe_model_id(value: Any) -> str:
    text = _safe_text(value).lower()
    return re.sub(r"[^a-z0-9_./:-]+", "-", text).strip("-")[:160]


def _safe_status(value: Any) -> str:
    text = _safe_text(value).lower().replace("-", "_")
    return text if text in {"success", "cached", "dry_run", "timeout", "provider_error", "client_error", "blocked"} else "success"


def _safe_error_category(value: Any) -> str:
    text = _safe_text(value).lower().replace("-", "_")
    allowed = {"none", "cached", "rate_limited", "timeout", "provider_5xx", "client_4xx", "unknown"}
    return text if text in allowed else "none"


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return max(0, min(int(value), 2_000_000))
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return max(0.0, min(float(value), 1000.0))
    except (TypeError, ValueError):
        return None


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "request"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _check(check_id: str, status: str, reason: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": status,
        "reason": reason,
        "evidence_count": len(evidence),
        "evidence": evidence[:12],
    }
