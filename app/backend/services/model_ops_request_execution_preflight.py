from __future__ import annotations

import re
from typing import Any

from services.model_budget import normalize_budget_task
from services.model_catalog import canonical_model_id, estimate_token_cost_usd, model_profile
from services.model_default_candidate_selector import ModelDefaultCandidateSelectorService
from services.model_request_cost_bounds import REQUEST_COST_BOUNDS
from services.model_request_policy import resolve_generation_request_policy
from services.model_runtime_router import resolve_runtime_model


HIGH_FREQUENCY_TASKS = {"fast", "ocr", "classification", "embedding"}
SAFE_REQUEST_FIELD_PATTERN = re.compile(
    r"(authorization|api[_-]?key|app_ai_key|headers|messages|prompt|payload|"
    r"request_body|response_body|raw_output|model_output|generated_text|candidate_text|"
    r"document_text|legal_text|email|phone|identity|password|secret)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization)",
    re.IGNORECASE,
)


class ModelOpsRequestExecutionPreflightService:
    """Evaluate sanitized per-request budget and cheap-first execution readiness."""

    def __init__(self, *, selector: ModelDefaultCandidateSelectorService | None = None) -> None:
        self.selector = selector or ModelDefaultCandidateSelectorService()

    def build_preflight(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        forbidden_field_count = self._forbidden_field_count(data)
        rows = [self._request_row(index, request) for index, request in enumerate(self._requests(data), start=1)]
        checks = self._checks(rows, forbidden_field_count)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]

        return {
            "id": "modelops-request-execution-preflight",
            "title": "ModelOps request execution preflight",
            "status": "blocked" if blocking else ("review_required" if warnings else "ready"),
            "method": {
                "type": "metadata-only-request-execution-preflight",
                "notes": [
                    "Evaluates sanitized single-request execution metadata before a NewAPI/Gemini call is made.",
                    "Combines runtime model resolution, cheap-first fallback ordering, estimated input/output tokens, local catalog pricing, and task cost limits.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
            },
            "summary": {
                "request_count": len(rows),
                "ready_request_count": sum(1 for row in rows if row["execution_status"] == "ready"),
                "review_request_count": sum(1 for row in rows if row["execution_status"] == "review_required"),
                "blocked_request_count": sum(1 for row in rows if row["execution_status"] == "blocked"),
                "high_frequency_request_count": sum(1 for row in rows if row["high_frequency_task"]),
                "cheap_first_ready_count": sum(
                    1 for row in rows if row["high_frequency_task"] and row["cheap_first_aligned"]
                ),
                "local_downgrade_count": sum(1 for row in rows if row["routed_to_recommended_model"]),
                "unknown_price_count": sum(1 for row in rows if row["estimated_request_cost_usd"] is None),
                "estimated_cost_usd_sum": round(
                    sum(row["estimated_request_cost_usd"] or 0.0 for row in rows),
                    8,
                ),
                "forbidden_payload_field_count": forbidden_field_count,
                "raw_payload_echoed": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "credentials_included": False,
            },
            "request_rows": rows,
            "checks": checks,
            "blocking_check_ids": blocking,
            "warning_check_ids": warnings,
            "execution_policy": {
                "cheap_first_policy": "High-frequency tasks must resolve to the cheapest stable Gemini-capable default before provider execution.",
                "fallback_policy": "Fallback chains must start with a stable low-cost Gemini option; premium and unknown-price candidates remain review-only.",
                "cost_policy": "A request is blocked when estimated catalog cost exceeds the task fail bound or a supplied max_cost_usd.",
                "runtime_policy": "Local runtime routing may downgrade unsafe explicit models to the task recommendation before execution.",
            },
            "privacy_boundary": {
                "metadata_only": True,
                "raw_payload_echoed": False,
                "request_body_included": False,
                "headers_included": False,
                "prompts_included": False,
                "raw_legal_text_included": False,
                "raw_model_output_included": False,
                "credentials_included": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "output_scope": "task labels, sanitized model ids, runtime route decisions, token estimates, local catalog costs, fallback cost tiers, reason codes, and release actions only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_gateway_inventory_claimed": False,
                "pricing_accuracy_claimed": False,
                "model_quality_claimed": False,
                "automatic_default_change_claimed": False,
                "request_sent": False,
            },
            "recommended_actions": self._recommended_actions(rows, forbidden_field_count),
            "validation_commands": [
                "python -m pytest tests/test_model_ops_request_execution_preflight.py tests/test_model_runtime_router.py tests/test_model_request_cost_bounds.py -q",
                "python -m pytest tests/test_model_gateway_request_compatibility_gate.py tests/test_model_ops_readiness.py tests/test_frontend_ui_regression_gate.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _requests(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        supplied = data.get("requests")
        if isinstance(supplied, list) and supplied:
            return [item if isinstance(item, dict) else {"model": item} for item in supplied[:40]]
        return [
            {"id": "fast-default", "task": "fast", "model": "auto", "estimated_input_tokens": 1200},
            {"id": "classification-default", "task": "classification", "model": "auto", "estimated_input_tokens": 1600},
            {"id": "review-balanced", "task": "review", "model": "auto", "estimated_input_tokens": 22000},
            {"id": "agentic-cheap-first", "task": "agentic", "model": "auto", "estimated_input_tokens": 8000},
            {"id": "embedding-default", "task": "embedding", "model": "auto-embedding", "estimated_input_tokens": 25000},
        ]

    def _request_row(self, index: int, request: dict[str, Any]) -> dict[str, Any]:
        task = normalize_budget_task(_safe_text(request.get("task")) or "fast")
        request_id = _safe_text(request.get("id")) or f"{task}-{index}"
        requested_model = _safe_model_id(request.get("model")) or "auto"
        allow_over_budget = request.get("allow_over_budget_model") is True
        route = resolve_runtime_model(
            requested_model,
            task=task,
            allow_over_budget_model=allow_over_budget,
        )
        canonical = canonical_model_id(route.resolved_model)
        profile = model_profile(route.resolved_model)
        request_policy = resolve_generation_request_policy(
            task=task,
            requested_max_tokens=_safe_int(request.get("estimated_output_tokens"))
            or _safe_int(request.get("max_tokens")),
        )
        estimated_input_tokens = self._estimated_input_tokens(task, request)
        estimated_output_tokens = self._estimated_output_tokens(task, request, request_policy)
        estimated_cost = estimate_token_cost_usd(route.resolved_model, estimated_input_tokens, estimated_output_tokens)
        cost_limit = self._cost_limit(task, request)
        fallback_rows = self._fallback_rows(task, request)
        reason_codes = self._reason_codes(
            task=task,
            route=route,
            profile=profile,
            estimated_cost=estimated_cost,
            cost_limit=cost_limit,
            fallback_rows=fallback_rows,
        )
        execution_status = self._execution_status(reason_codes)
        return {
            "id": f"request-execution-preflight-{_slug(request_id)}",
            "request_id": request_id,
            "task": route.task,
            "requested_model": route.requested_model,
            "resolved_model": route.resolved_model,
            "canonical_model": canonical,
            "known_catalog_model": route.is_known_model,
            "cost_tier": route.cost_tier or "unknown",
            "max_cost_tier": route.max_cost_tier,
            "budget_mode": route.budget_mode,
            "allow_over_budget_model": route.allow_over_budget_model,
            "requires_operator_review": route.requires_operator_review,
            "routed_to_recommended_model": route.routed_to_recommended_model,
            "recommended_model": route.recommended_model,
            "high_frequency_task": route.task in HIGH_FREQUENCY_TASKS,
            "cheap_first_aligned": self._cheap_first_aligned(route),
            "estimated_input_tokens": estimated_input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_total_tokens": estimated_input_tokens + estimated_output_tokens,
            "estimated_request_cost_usd": estimated_cost,
            "request_cost_limit_usd": cost_limit,
            "pricing_estimate_available": estimated_cost is not None,
            "request_policy": {
                "effective_max_tokens": request_policy.effective_max_tokens,
                "max_tokens_adjusted": request_policy.max_tokens_adjusted,
                "cost_mode": request_policy.cost_mode,
            },
            "fallback_rows": fallback_rows,
            "execution_status": execution_status,
            "release_action": self._release_action(execution_status, reason_codes),
            "reason_codes": reason_codes,
            "next_action": self._next_action(execution_status, reason_codes),
        }

    def _fallback_rows(self, task: str, request: dict[str, Any]) -> list[dict[str, Any]]:
        supplied = request.get("fallback_chain")
        if isinstance(supplied, list) and supplied:
            models = [_safe_model_id(item) for item in supplied[:8]]
            models = [model for model in models if model]
        else:
            models = [
                str(row.get("model") or "")
                for row in self.selector.default_ladder_for_task(task, limit=4)
            ]
        rows: list[dict[str, Any]] = []
        for order, model in enumerate(models[:8], start=1):
            profile = model_profile(model)
            rows.append(
                {
                    "order": order,
                    "model": model,
                    "canonical_model": canonical_model_id(model),
                    "known_catalog_model": profile is not None,
                    "cost_tier": profile.cost_tier if profile else "unknown",
                    "catalog_status": profile.status if profile else "unknown",
                    "cheap_first_candidate": self._model_is_cheap_first(model, profile),
                    "premium_candidate": (profile.cost_tier == "premium") if profile else False,
                    "pricing_estimate_available": profile is not None
                    and (
                        profile.input_usd_per_million_tokens is not None
                        or profile.output_usd_per_million_tokens is not None
                    ),
                }
            )
        return rows

    def _reason_codes(
        self,
        *,
        task: str,
        route: Any,
        profile: Any,
        estimated_cost: float | None,
        cost_limit: float,
        fallback_rows: list[dict[str, Any]],
    ) -> list[str]:
        codes = list(route.reason_codes)
        if profile is None:
            codes.append("unknown_catalog_model")
        if estimated_cost is None:
            codes.append("pricing_estimate_unavailable")
        elif estimated_cost > cost_limit:
            codes.append("estimated_cost_over_limit")
        if task in HIGH_FREQUENCY_TASKS and not self._cheap_first_aligned(route):
            codes.append("high_frequency_not_cheap_first_aligned")
        if route.allow_over_budget_model and (route.is_over_budget or route.requires_operator_review):
            codes.append("explicit_over_budget_review_exception")
        if not fallback_rows:
            codes.append("fallback_chain_missing")
        elif task in HIGH_FREQUENCY_TASKS and not fallback_rows[0]["cheap_first_candidate"]:
            codes.append("fallback_chain_not_cheap_first")
        if any(row["premium_candidate"] for row in fallback_rows[:2]) and task in HIGH_FREQUENCY_TASKS:
            codes.append("premium_fallback_before_cheap_first_exhausted")
        if any(not row["known_catalog_model"] for row in fallback_rows):
            codes.append("fallback_chain_unknown_model")
        return _dedupe(codes) or ["request_execution_preflight_ready"]

    def _execution_status(self, reason_codes: list[str]) -> str:
        blocking = {
            "unknown_catalog_model",
            "pricing_estimate_unavailable",
            "estimated_cost_over_limit",
            "high_frequency_not_cheap_first_aligned",
            "fallback_chain_missing",
            "fallback_chain_not_cheap_first",
            "premium_fallback_before_cheap_first_exhausted",
            "fallback_chain_unknown_model",
        }
        if any(code in blocking for code in reason_codes):
            return "blocked"
        review = {
            "explicit_over_budget_review_exception",
            "operator_review_required",
            "explicit_over_budget_allowed",
            "explicit_gateway_passthrough_allowed",
        }
        if any(code in review for code in reason_codes):
            return "review_required"
        return "ready"

    def _checks(self, rows: list[dict[str, Any]], forbidden_field_count: int) -> list[dict[str, Any]]:
        blocked = [row["id"] for row in rows if row["execution_status"] == "blocked"]
        review = [row["id"] for row in rows if row["execution_status"] == "review_required"]
        high_frequency_gaps = [
            row["id"]
            for row in rows
            if row["high_frequency_task"] and not row["cheap_first_aligned"]
        ]
        cost_gaps = [
            row["id"]
            for row in rows
            if "estimated_cost_over_limit" in row["reason_codes"]
            or "pricing_estimate_unavailable" in row["reason_codes"]
        ]
        fallback_gaps = [
            row["id"]
            for row in rows
            if any(code.startswith("fallback_chain") or code.startswith("premium_fallback") for code in row["reason_codes"])
        ]
        return [
            _check(
                "sanitized-execution-metadata-only",
                "fail" if forbidden_field_count else "pass",
                "Input contains no raw prompt, message, header, payload, legal text, model output, credential, email, or identity fields.",
                [str(forbidden_field_count)],
            ),
            _check(
                "cheap-first-before-execution",
                "fail" if high_frequency_gaps else "pass",
                "High-frequency requests resolve to cheap-first Gemini defaults before provider execution.",
                high_frequency_gaps,
            ),
            _check(
                "request-cost-within-bounds",
                "fail" if cost_gaps else "pass",
                "Estimated local catalog request costs stay within task or supplied request limits.",
                cost_gaps,
            ),
            _check(
                "fallback-chain-cost-ordered",
                "fail" if fallback_gaps else "pass",
                "Fallback chains begin with known low-cost candidates and keep premium/unknown models review-only.",
                fallback_gaps,
            ),
            _check(
                "request-review-exceptions-visible",
                "warn" if review else "pass",
                "Explicit over-budget execution exceptions remain visible for maintainer review.",
                review,
            ),
            _check(
                "no-provider-side-effects",
                "pass",
                "The preflight does not call providers, gateways, models, app AI endpoints, or the network and does not write configuration.",
                [],
            ),
            _check(
                "all-request-rows-ready",
                "fail" if blocked else ("warn" if review else "pass"),
                "Every submitted request row has a release action before execution.",
                blocked + review,
            ),
        ]

    def _recommended_actions(self, rows: list[dict[str, Any]], forbidden_field_count: int) -> list[str]:
        if forbidden_field_count:
            return [
                "Discard raw request payloads and resubmit only task, model, fallback_chain, estimated token, max_cost_usd, and allow_over_budget metadata.",
                "Do not include headers, prompts, legal text, model output, emails, identifiers, or credentials in request execution evidence.",
            ]
        blocked = [row for row in rows if row["execution_status"] == "blocked"]
        if blocked:
            return [
                "Do not send blocked request rows to NewAPI/Gemini until cost, model, and fallback-chain issues are resolved.",
                "Keep high-frequency work on Flash-Lite or the cheapest stable Gemini embedding default before any provider execution.",
            ]
        review = [row for row in rows if row["execution_status"] == "review_required"]
        if review:
            return [
                "Require maintainer approval before sending explicit over-budget request rows.",
                "Attach request execution preflight output to canary or release evidence before expanding traffic.",
            ]
        return [
            "Request execution metadata is ready for cheap-first review without sending a provider request.",
            "Keep this preflight in front of runtime calls when changing model defaults, token caps, or fallback order.",
        ]

    def _estimated_input_tokens(self, task: str, request: dict[str, Any]) -> int:
        supplied = _safe_int(request.get("estimated_input_tokens"))
        if supplied is not None:
            return max(0, min(supplied, 2_000_000))
        bound = REQUEST_COST_BOUNDS.get(task)
        return bound.prompt_tokens if bound else 2_000

    def _estimated_output_tokens(self, task: str, request: dict[str, Any], request_policy: Any) -> int:
        supplied = _safe_int(request.get("estimated_output_tokens"))
        if supplied is not None:
            return max(0, min(supplied, 1_000_000))
        supplied_max = _safe_int(request.get("max_tokens"))
        if supplied_max is not None:
            return max(0, min(supplied_max, 1_000_000))
        if task == "embedding":
            return 0
        return max(0, int(request_policy.effective_max_tokens))

    def _cost_limit(self, task: str, request: dict[str, Any]) -> float:
        supplied = _safe_float(request.get("max_cost_usd"))
        if supplied is not None:
            return max(0.0, min(supplied, 1000.0))
        bound = REQUEST_COST_BOUNDS.get(task)
        return bound.fail_default_cost_usd if bound else 0.05

    def _cheap_first_aligned(self, route: Any) -> bool:
        if route.task not in HIGH_FREQUENCY_TASKS:
            return True
        profile = model_profile(route.resolved_model)
        return self._model_is_cheap_first(route.resolved_model, profile)

    def _model_is_cheap_first(self, model: str, profile: Any) -> bool:
        canonical = canonical_model_id(model) or model
        if "embedding" in canonical:
            return bool(profile and profile.cost_tier in {"lowest", "low"})
        return "flash-lite" in canonical and bool(profile and profile.cost_tier in {"lowest", "low"})

    def _release_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "allow_metadata_reviewed_request"
        if status == "review_required":
            return "require_operator_review_before_request"
        if "estimated_cost_over_limit" in reason_codes or "pricing_estimate_unavailable" in reason_codes:
            return "block_request_until_cost_bound_is_safe"
        if "high_frequency_not_cheap_first_aligned" in reason_codes:
            return "block_request_until_cheap_first_model_resolves"
        return "block_request_until_preflight_passes"

    def _next_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "Keep this request behind cheap-first execution review; this gate sends no provider request."
        if status == "review_required":
            return "Require maintainer approval before sending this explicit over-budget or passthrough request."
        return f"Do not send this request until preflight issues are fixed: {', '.join(reason_codes[:6])}."

    def _forbidden_field_count(self, value: Any) -> int:
        return min(20, len(self._forbidden_hits(value)))

    def _forbidden_hits(self, value: Any) -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if SAFE_REQUEST_FIELD_PATTERN.search(str(key)):
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


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if SENSITIVE_VALUE_PATTERN.search(text):
        return ""
    return re.sub(r"[\r\n\t]+", " ", text)[:180]


def _safe_model_id(value: Any) -> str:
    text = _safe_text(value).lower()
    if text in {"auto", "default", "none", ""}:
        return text
    return re.sub(r"[^a-z0-9_./:-]+", "-", text).strip("-")[:160]


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
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
