from __future__ import annotations

import re
from typing import Any

from services.model_budget import normalize_budget_task
from services.model_catalog import canonical_model_id, model_profile
from services.model_runtime_router import resolve_runtime_model
from services.modelops_observed_gateway_model_fit_matrix import ModelOpsObservedGatewayModelFitMatrixService


SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization)",
    re.IGNORECASE,
)
FORBIDDEN_FIELD_PATTERN = re.compile(
    r"(authorization|api[_-]?key|app_ai_key|headers|messages|prompt|payload|"
    r"request_body|response_body|raw_output|model_output|generated_text|candidate_text|"
    r"document_text|legal_text|email|phone|identity)",
    re.IGNORECASE,
)
HIGH_FREQUENCY_TASKS = {"fast", "ocr", "classification"}


class ModelOpsRuntimeExplicitModelFitGateService:
    """Expose runtime explicit-model fit risks without changing live routing."""

    def build_gate(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        forbidden_field_count = self._forbidden_field_count(data)
        observed_matrix = self._observed_matrix(data)
        observed_task_fit = {
            row["task"]: row
            for row in observed_matrix.get("task_fit_rows", [])
            if isinstance(row, dict) and row.get("task")
        }
        rows = [
            self._scenario_row(index, scenario, observed_task_fit)
            for index, scenario in enumerate(self._scenarios(data), start=1)
        ]
        checks = self._checks(rows, forbidden_field_count)
        blocking = [check["id"] for check in checks if check["status"] == "fail"]
        warnings = [check["id"] for check in checks if check["status"] == "warn"]

        return {
            "id": "modelops-runtime-explicit-model-fit-gate",
            "title": "Runtime explicit model fit gate",
            "status": "blocked" if blocking else ("review_required" if warnings else "ready"),
            "method": {
                "type": "metadata-only-runtime-explicit-model-fit-gate",
                "notes": [
                    "Runs local runtime routing decisions against sanitized explicit-model scenarios without sending provider requests.",
                    "Highlights unknown gateway pass-through, explicit over-budget allowance, premium review, and cheap-first downgrade behavior before release.",
                    "Links each task to observed gateway model-fit status when sanitized inventory evidence is available.",
                    "Does not call NewAPI, Gemini, OpenAI, Google, gateways, app AI endpoints, models, or the network.",
                ],
            },
            "summary": {
                "scenario_count": len(rows),
                "ready_row_count": sum(1 for row in rows if row["runtime_fit_status"] == "ready"),
                "enforced_row_count": sum(1 for row in rows if row["runtime_fit_status"] == "enforced"),
                "review_row_count": sum(1 for row in rows if row["runtime_fit_status"] == "review_required"),
                "blocked_row_count": sum(1 for row in rows if row["runtime_fit_status"] == "blocked"),
                "unknown_gateway_passthrough_count": sum(1 for row in rows if row["unknown_gateway_passthrough"]),
                "explicit_over_budget_allowed_count": sum(1 for row in rows if row["explicit_over_budget_allowed"]),
                "downgraded_to_recommended_count": sum(1 for row in rows if row["routed_to_recommended_model"]),
                "cheap_first_enforced_count": sum(1 for row in rows if row["cheap_first_aligned"]),
                "observed_fit_review_count": sum(1 for row in rows if row["observed_fit_status"] in {"missing", "review_only"}),
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
            "runtime_policy": {
                "unknown_model_policy": "Unknown gateway models may remain explicit pass-through at runtime, but they are review-required and cannot satisfy cheap-first release evidence.",
                "over_budget_policy": "Known over-budget models route to the task recommendation unless allow_over_budget_model is explicitly true.",
                "cheap_first_policy": "High-frequency tasks must resolve to stable lowest-cost defaults or a local downgrade before release.",
                "observed_fit_policy": "Observed gateway fit status is advisory metadata and never validates live account inventory.",
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
                "output_scope": "task labels, sanitized model ids, canonical ids, runtime route decisions, reason codes, observed fit states, and review actions only",
            },
            "claim_boundary": {
                "live_gateway_execution_claimed": False,
                "actual_gateway_inventory_claimed": False,
                "automatic_default_change_claimed": False,
                "runtime_behavior_changed": False,
                "pricing_accuracy_claimed": False,
                "model_quality_claimed": False,
            },
            "recommended_actions": self._recommended_actions(rows, forbidden_field_count),
            "validation_commands": [
                "python -m pytest tests/test_model_ops_runtime_explicit_model_fit_gate.py tests/test_model_runtime_router.py -q",
                "python -m pytest tests/test_aihub_runtime_routing.py tests/test_model_ops_readiness.py -q",
                "cd ../frontend && npm run typecheck && npm run ui:regression",
            ],
        }

    def _observed_matrix(self, data: dict[str, Any]) -> dict[str, Any]:
        supplied = data.get("observed_gateway_model_fit_matrix")
        if isinstance(supplied, dict):
            return supplied
        observed_models = data.get("observed_models")
        payload = {"observed_models": observed_models} if observed_models is not None else {}
        return ModelOpsObservedGatewayModelFitMatrixService().build_matrix(payload)

    def _scenarios(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        supplied = data.get("request_scenarios")
        if isinstance(supplied, list) and supplied:
            return [item if isinstance(item, dict) else {"model": item} for item in supplied[:40]]
        return [
            {"id": "fast-default", "task": "fast", "model": "auto", "endpoint": "gentxt"},
            {"id": "fast-premium-downgrade", "task": "fast", "model": "gemini-2.5-pro", "endpoint": "gentxt"},
            {
                "id": "fast-premium-explicit-allow",
                "task": "fast",
                "model": "gemini-2.5-pro",
                "allow_over_budget_model": True,
                "endpoint": "gentxt",
            },
            {
                "id": "classification-unknown-gateway",
                "task": "classification",
                "model": "yibu/gemini-9.9-flash-lite",
                "endpoint": "gentxt",
            },
            {"id": "review-balanced-default", "task": "review", "model": "auto", "endpoint": "gentxt"},
            {"id": "pdf-premium-exception", "task": "pdf", "model": "auto", "endpoint": "analyzepdf"},
            {"id": "image-explicit-media", "task": "image", "model": "auto", "endpoint": "genimg"},
            {"id": "agentic-low-cost-default", "task": "agentic", "model": "auto", "endpoint": "gentxt"},
            {
                "id": "grounded-research-low-cost-default",
                "task": "grounded-research",
                "model": "auto",
                "endpoint": "gentxt",
            },
        ]

    def _scenario_row(
        self,
        index: int,
        scenario: dict[str, Any],
        observed_task_fit: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        task = normalize_budget_task(_safe_text(scenario.get("task")) or "fast")
        model = _safe_model_id(scenario.get("model")) or None
        allow_over_budget = bool(scenario.get("allow_over_budget_model") is True)
        route = resolve_runtime_model(model, task=task, allow_over_budget_model=allow_over_budget)
        canonical = canonical_model_id(route.resolved_model)
        profile = model_profile(route.resolved_model)
        observed = observed_task_fit.get(route.task) or {}
        reason_codes = self._reason_codes(route, observed, profile)
        runtime_fit_status = self._runtime_fit_status(reason_codes, route)
        endpoint = _safe_text(scenario.get("endpoint")) or "gentxt"
        scenario_id = _safe_text(scenario.get("id")) or f"{route.task}-{index}"
        return {
            "id": f"runtime-explicit-fit-{_slug(scenario_id)}",
            "scenario_id": scenario_id,
            "endpoint": endpoint,
            "task": route.task,
            "requested_model": route.requested_model,
            "requested_resolved_model": route.requested_resolved_model,
            "resolved_model": route.resolved_model,
            "canonical_model": canonical,
            "known_catalog_model": route.is_known_model,
            "cost_tier": route.cost_tier or "unknown",
            "max_cost_tier": route.max_cost_tier,
            "budget_mode": route.budget_mode,
            "allow_over_budget_model": route.allow_over_budget_model,
            "requires_operator_review": route.requires_operator_review,
            "is_over_budget": route.is_over_budget,
            "routed_to_recommended_model": route.routed_to_recommended_model,
            "recommended_model": route.recommended_model,
            "unknown_gateway_passthrough": "gateway_passthrough" in route.reason_codes,
            "explicit_over_budget_allowed": "explicit_over_budget_allowed" in route.reason_codes,
            "cheap_first_aligned": self._cheap_first_aligned(route),
            "observed_fit_status": str(observed.get("gateway_fit_status") or "not_supplied"),
            "observed_cheapest_gateway_model": observed.get("cheapest_gateway_model"),
            "observed_cheapest_canonical_model": observed.get("cheapest_canonical_model"),
            "runtime_fit_status": runtime_fit_status,
            "reason_codes": reason_codes,
            "route_reason_codes": list(route.reason_codes),
            "next_action": self._next_action(runtime_fit_status, reason_codes),
        }

    def _reason_codes(self, route: Any, observed: dict[str, Any], profile: Any) -> list[str]:
        codes = list(route.reason_codes)
        observed_status = str(observed.get("gateway_fit_status") or "")
        if route.task in HIGH_FREQUENCY_TASKS and not self._cheap_first_aligned(route):
            codes.append("high_frequency_not_cheap_first_aligned")
        if route.allow_over_budget_model and (route.is_over_budget or route.requires_operator_review):
            codes.append("explicit_over_budget_runtime_exception")
        if "gateway_passthrough" in route.reason_codes:
            codes.append("unknown_gateway_runtime_passthrough")
        if profile and getattr(profile, "status", "") != "stable":
            codes.append("runtime_model_not_stable")
        if observed_status in {"missing", "review_only"}:
            codes.append(f"observed_gateway_fit_{observed_status}")
        if observed_status == "not_supplied":
            codes.append("observed_gateway_fit_not_supplied")
        return _dedupe(codes) or ["runtime_explicit_model_fit_ready"]

    def _runtime_fit_status(self, reason_codes: list[str], route: Any) -> str:
        blocking = {"runtime_model_not_stable"}
        if any(code in blocking for code in reason_codes):
            return "blocked"
        if route.routed_to_recommended_model:
            return "enforced"
        review = {
            "unknown_gateway_runtime_passthrough",
            "explicit_over_budget_runtime_exception",
            "high_frequency_not_cheap_first_aligned",
            "observed_gateway_fit_missing",
            "observed_gateway_fit_review_only",
            "observed_gateway_fit_not_supplied",
            "operator_review_required",
        }
        if any(code in review for code in reason_codes):
            return "review_required"
        return "ready"

    def _cheap_first_aligned(self, route: Any) -> bool:
        if route.task not in HIGH_FREQUENCY_TASKS:
            return True
        canonical = canonical_model_id(route.resolved_model) or route.resolved_model
        return "flash-lite" in canonical and route.cost_tier in {"lowest", "low"}

    def _checks(self, rows: list[dict[str, Any]], forbidden_field_count: int) -> list[dict[str, Any]]:
        unknown_rows = [row["id"] for row in rows if row["unknown_gateway_passthrough"]]
        explicit_over_budget_rows = [row["id"] for row in rows if row["explicit_over_budget_allowed"]]
        high_frequency_gaps = [
            row["id"]
            for row in rows
            if row["task"] in HIGH_FREQUENCY_TASKS and not row["cheap_first_aligned"]
        ]
        observed_review_rows = [
            row["id"]
            for row in rows
            if row["observed_fit_status"] in {"missing", "review_only", "not_supplied"}
        ]
        return [
            _check(
                "sanitized-runtime-scenarios-only",
                "fail" if forbidden_field_count else "pass",
                "Runtime explicit model fit input contains no raw request, prompt, response, header, or credential fields.",
                [str(forbidden_field_count)],
            ),
            _check(
                "unknown-gateway-passthrough-visible",
                "warn" if unknown_rows else "pass",
                "Unknown gateway pass-through scenarios are visible and remain review-required.",
                unknown_rows,
            ),
            _check(
                "explicit-over-budget-boundary",
                "warn" if explicit_over_budget_rows else "pass",
                "Explicitly allowed over-budget routes remain review exceptions, not defaults.",
                explicit_over_budget_rows,
            ),
            _check(
                "high-frequency-cheap-first-enforced",
                "warn" if high_frequency_gaps else "pass",
                "High-frequency runtime scenarios resolve to cheap-first aligned models, local downgrades, or explicit reviewed exceptions.",
                high_frequency_gaps,
            ),
            _check(
                "observed-gateway-fit-linked",
                "warn" if observed_review_rows else "pass",
                "Runtime scenarios are linked to observed gateway fit evidence where available.",
                observed_review_rows,
            ),
            _check(
                "no-runtime-side-effects",
                "pass",
                "The gate does not call providers, gateways, models, app AI endpoints, or the network and does not write configuration.",
                [],
            ),
        ]

    def _recommended_actions(self, rows: list[dict[str, Any]], forbidden_field_count: int) -> list[str]:
        if forbidden_field_count:
            return [
                "Discard raw request payloads and submit sanitized task/model/allow_over_budget metadata only.",
                "Do not include headers, prompts, legal text, model output, credentials, emails, or identifiers in runtime fit evidence.",
            ]
        if any(row["unknown_gateway_passthrough"] for row in rows):
            return [
                "Keep unknown gateway pass-through models explicit-only until catalog price, lifecycle, task fit, and gateway behavior are reviewed.",
                "Use cheap-first defaults for high-frequency traffic and reserve allow_over_budget_model for reviewed exceptions.",
            ]
        if any(row["explicit_over_budget_allowed"] for row in rows):
            return [
                "Review explicit over-budget runtime exceptions before they influence defaults.",
                "Attach route telemetry and benchmark evidence before expanding premium exceptions.",
            ]
        return [
            "Runtime explicit model fit scenarios are ready for maintainer review.",
            "Continue monitoring route telemetry for unknown-price or allowed-over-budget drift.",
        ]

    def _next_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "Keep this runtime route as reviewed metadata; no provider request is sent by this gate."
        if status == "enforced":
            return "Runtime enforcement routes this request to the task recommendation before provider execution."
        if status == "review_required":
            return "Review explicit model fit, catalog price/status, and observed gateway coverage before relying on this route."
        return f"Block release reliance until runtime fit issues are resolved: {', '.join(reason_codes[:5])}."

    def _forbidden_field_count(self, value: Any) -> int:
        return min(20, len(self._forbidden_hits(value)))

    def _forbidden_hits(self, value: Any) -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"observed_gateway_model_fit_matrix", "observed_models"}:
                    continue
                if FORBIDDEN_FIELD_PATTERN.search(str(key)):
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


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "scenario"


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
