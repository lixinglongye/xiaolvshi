from __future__ import annotations

import re
from typing import Any

from services.gemini_newapi_observed_model_extraction import safe_model_id
from services.legal_document_benchmark_route_plan_execution_readiness import (
    LegalDocumentBenchmarkRoutePlanExecutionReadinessService,
)


ARCHIVE_ID = "legal-document-benchmark-route-plan-execution-result-archive"
FORBIDDEN_FIELD_PATTERN = re.compile(
    r"(authorization|api[_-]?key|credential|headers|message|prompt|payload|request_body|"
    r"response_body|gateway_response|raw_output|model_output|generated_text|candidate_text|"
    r"document_text|legal_text|fixture_snippet|benchmark_sample|email|phone|identity|password|secret)",
    re.IGNORECASE,
)
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|\bbearer\s+[A-Za-z0-9._-]{10,}|"
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|password|secret|api[_-]?key|authorization)",
    re.IGNORECASE,
)
SAFE_OBSERVATION_FIELDS = [
    "case_id",
    "phase",
    "observed_model",
    "observed_status",
    "observed_cost_usd",
    "observed_input_tokens",
    "observed_output_tokens",
    "latency_ms",
    "fallback_used",
    "error_category",
]


class LegalDocumentBenchmarkRoutePlanExecutionResultArchiveService:
    """Archive sanitized manual execution metadata for legal-document route-plan runs."""

    def __init__(
        self,
        readiness_service: LegalDocumentBenchmarkRoutePlanExecutionReadinessService | None = None,
    ) -> None:
        self.readiness_service = readiness_service or LegalDocumentBenchmarkRoutePlanExecutionReadinessService()

    def build_archive(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        readiness_payload = data.get("execution_readiness") if isinstance(data.get("execution_readiness"), dict) else None
        readiness = self.readiness_service.build_packet(readiness_payload)
        route_plan = self.readiness_service.route_plan_service.build_plan(
            self._route_plan_payload(readiness_payload or data)
        )
        route_rows = {str(row["case_id"]): row for row in route_plan.get("case_route_rows", [])}
        observations = self._observations(data)
        forbidden_field_count = self._forbidden_field_count(data)
        archive_rows = [
            self._archive_row(index, observation, route_rows)
            for index, observation in enumerate(observations, start=1)
        ]
        checks = self._checks(readiness, archive_rows, forbidden_field_count)
        blocking_check_ids = [check["id"] for check in checks if check["status"] == "fail"]
        warning_check_ids = [check["id"] for check in checks if check["status"] == "warn"]
        status = self._status(archive_rows, blocking_check_ids, warning_check_ids)

        return {
            "id": ARCHIVE_ID,
            "title": "Legal document benchmark route-plan execution result archive",
            "status": status,
            "method": {
                "type": "metadata-only-route-plan-execution-result-archive",
                "notes": [
                    "Archives externally supplied manual execution metadata after route-plan readiness review.",
                    "Compares observed case/model/cost/latency rows with the cheap-first route plan.",
                    "Does not call NewAPI, Gemini, gateways, app AI endpoints, public datasets, or the network.",
                ],
            },
            "summary": {
                "readiness_status": readiness["status"],
                "manual_execution_ready": readiness["summary"]["manual_execution_ready"],
                "route_plan_status": route_plan["status"],
                "route_plan_case_count": route_plan["summary"]["case_count"],
                "recommended_fixture_limit": readiness["manual_run_packet"]["recommended_fixture_limit"],
                "max_parallel_model_requests": readiness["manual_run_packet"]["max_parallel_model_requests"],
                "observation_count": len(archive_rows),
                "archived_case_count": len({row["case_id"] for row in archive_rows if row["case_id"]}),
                "ready_observation_count": sum(1 for row in archive_rows if row["result_status"] == "ready"),
                "review_observation_count": sum(
                    1 for row in archive_rows if row["result_status"] == "review_required"
                ),
                "blocked_observation_count": sum(1 for row in archive_rows if row["result_status"] == "blocked"),
                "matched_route_case_count": sum(1 for row in archive_rows if row["route_plan_match"]),
                "cheap_first_aligned_count": sum(1 for row in archive_rows if row["cheap_first_aligned"]),
                "fallback_used_count": sum(1 for row in archive_rows if row["fallback_used"]),
                "observed_cost_usd_sum": round(sum(row["observed_cost_usd"] or 0.0 for row in archive_rows), 8),
                "observed_token_count": sum(row["observed_total_tokens"] or 0 for row in archive_rows),
                "forbidden_payload_field_count": forbidden_field_count,
                "raw_payload_echoed": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
                "benchmark_execution_claimed": False,
            },
            "archive_rows": archive_rows,
            "checks": checks,
            "blocking_check_ids": blocking_check_ids,
            "warning_check_ids": warning_check_ids,
            "source_summaries": {
                "execution_readiness": {
                    "id": readiness["id"],
                    "status": readiness["status"],
                    "manual_execution_ready": readiness["summary"]["manual_execution_ready"],
                    "blocking_gate_count": readiness["summary"]["blocking_gate_count"],
                    "warning_gate_count": readiness["summary"]["warning_gate_count"],
                },
                "route_plan": {
                    "id": route_plan["id"],
                    "status": route_plan["status"],
                    "case_count": route_plan["summary"]["case_count"],
                    "premium_primary_case_count": route_plan["summary"]["premium_primary_case_count"],
                    "estimated_primary_cost_usd": route_plan["summary"]["estimated_primary_cost_usd"],
                },
            },
            "archive_policy": {
                "accepted_observation_fields": SAFE_OBSERVATION_FIELDS,
                "default_execution_mode": readiness["manual_run_packet"]["default_execution_mode"],
                "default_model_strategy": readiness["manual_run_packet"]["default_model_strategy"],
                "requires_pre_execution_readiness": True,
                "requires_sanitized_external_observations": True,
                "requires_fixture_limit": True,
                "records_maintainer_approval": False,
                "executes_benchmark": False,
                "writes_archive_file": False,
            },
            "privacy_boundary": {
                "metadata_only": True,
                "returns_case_ids": True,
                "returns_route_metadata": True,
                "returns_public_benchmark_text": False,
                "returns_fixture_snippets": False,
                "returns_raw_legal_text": False,
                "returns_prompts": False,
                "returns_request_bodies": False,
                "returns_response_bodies": False,
                "returns_headers": False,
                "returns_gateway_responses": False,
                "returns_model_outputs": False,
                "returns_credentials": False,
                "returns_emails": False,
                "model_called": False,
                "gateway_called": False,
                "network_called": False,
                "configuration_written": False,
                "traffic_shifted": False,
            },
            "claim_boundary": {
                "benchmark_executed_by_service": False,
                "live_gateway_execution_claimed": False,
                "public_benchmark_score_claimed": False,
                "production_quality_claimed": False,
                "maintainer_approval_claimed": False,
                "default_model_changed": False,
                "traffic_shifted": False,
                "allowed_claim": (
                    "Sanitized manual legal-document benchmark route observations were archived as metadata-only evidence."
                ),
            },
            "recommended_actions": self._recommended_actions(status, archive_rows, forbidden_field_count),
            "validation_commands": [
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_result_archive.py -q",
                "cd app/backend && python -m pytest tests/test_legal_document_benchmark_route_plan_execution_readiness.py tests/test_legal_document_benchmark_route_plan.py -q",
            ],
        }

    def _route_plan_payload(self, data: dict[str, Any]) -> dict[str, Any] | None:
        route_plan = data.get("route_plan")
        if isinstance(route_plan, dict):
            return route_plan
        if isinstance(data.get("case_route_overrides"), dict):
            return {"case_route_overrides": data.get("case_route_overrides")}
        return None

    def _observations(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        supplied = data.get("observations")
        if isinstance(supplied, list):
            return [item if isinstance(item, dict) else {"case_id": item} for item in supplied[:40]]
        if isinstance(supplied, dict):
            rows = []
            for case_id, value in sorted(supplied.items()):
                if isinstance(value, dict):
                    rows.append({"case_id": case_id, **value})
                else:
                    rows.append({"case_id": case_id, "observed_status": value})
            return rows[:40]
        return []

    def _archive_row(
        self,
        index: int,
        observation: dict[str, Any],
        route_rows: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        case_id = _safe_text(observation.get("case_id")) or f"case-{index}"
        route_row = route_rows.get(case_id)
        phase = _safe_phase(observation.get("phase"))
        observed_model = safe_model_id(
            observation.get("observed_model")
            or observation.get("resolved_model")
            or observation.get("model")
        )
        expected_model = self._expected_model(route_row, phase)
        observed_status = _safe_status(observation.get("observed_status") or observation.get("status"))
        observed_input_tokens = _safe_int(_first_present(observation, "observed_input_tokens", "input_tokens"))
        observed_output_tokens = _safe_int(_first_present(observation, "observed_output_tokens", "output_tokens"))
        observed_cost = _safe_float(_first_present(observation, "observed_cost_usd", "cost_usd"))
        latency_ms = _safe_int(observation.get("latency_ms"))
        fallback_used = observation.get("fallback_used") is True
        error_category = _safe_error_category(observation.get("error_category"))
        estimated_route_cost = self._estimated_route_cost(route_row, phase)
        reason_codes = self._reason_codes(
            route_row=route_row,
            phase=phase,
            observed_model=observed_model,
            expected_model=expected_model,
            observed_status=observed_status,
            observed_cost=observed_cost,
            estimated_route_cost=estimated_route_cost,
            latency_ms=latency_ms,
            fallback_used=fallback_used,
            error_category=error_category,
        )
        result_status = self._result_status(reason_codes)
        return {
            "id": f"route-plan-result-{_slug(case_id)}-{phase}",
            "case_id": case_id,
            "title": str(route_row.get("title") or "")[:160] if route_row else "",
            "document_type": str(route_row.get("document_type") or "")[:80] if route_row else "",
            "phase": phase,
            "route_plan_match": route_row is not None,
            "route_band": str(route_row.get("route_band") or "")[:80] if route_row else "",
            "expected_model": expected_model,
            "observed_model": observed_model,
            "cheap_first_aligned": bool(expected_model and observed_model == expected_model),
            "observed_status": observed_status,
            "observed_input_tokens": observed_input_tokens,
            "observed_output_tokens": observed_output_tokens,
            "observed_total_tokens": (observed_input_tokens or 0) + (observed_output_tokens or 0),
            "observed_cost_usd": observed_cost,
            "estimated_route_cost_usd": estimated_route_cost,
            "latency_ms": latency_ms,
            "fallback_used": fallback_used,
            "error_category": error_category,
            "result_status": result_status,
            "release_action": self._release_action(result_status, reason_codes),
            "reason_codes": reason_codes,
            "next_action": self._next_action(result_status, reason_codes),
        }

    def _expected_model(self, route_row: dict[str, Any] | None, phase: str) -> str:
        if not route_row:
            return ""
        if phase == "precheck":
            return str(route_row.get("precheck_route", {}).get("model") or "")
        return str(route_row.get("primary_route", {}).get("resolved_model") or "")

    def _estimated_route_cost(self, route_row: dict[str, Any] | None, phase: str) -> float | None:
        if not route_row:
            return None
        key = "estimated_precheck_cost_usd" if phase == "precheck" else "estimated_primary_cost_usd"
        value = route_row.get(key)
        return _safe_float(value)

    def _reason_codes(
        self,
        *,
        route_row: dict[str, Any] | None,
        phase: str,
        observed_model: str,
        expected_model: str,
        observed_status: str,
        observed_cost: float | None,
        estimated_route_cost: float | None,
        latency_ms: int | None,
        fallback_used: bool,
        error_category: str,
    ) -> list[str]:
        codes: list[str] = []
        if route_row is None:
            codes.append("missing_route_plan_case")
        if observed_status not in {"success", "cached", "dry_run"}:
            codes.append("observed_case_not_successful")
        if not observed_model:
            codes.append("observed_model_missing")
        elif expected_model and observed_model != expected_model:
            if fallback_used:
                codes.append("fallback_model_used")
            else:
                codes.append("observed_model_mismatch")
        if observed_cost is None:
            codes.append("observed_cost_missing")
        elif estimated_route_cost is not None and observed_cost > max(0.001, estimated_route_cost * 2.0):
            codes.append("observed_cost_over_route_budget")
        if latency_ms is None:
            codes.append("latency_missing")
        elif latency_ms > (10_000 if phase == "precheck" else 45_000):
            codes.append("latency_over_review_limit")
        if error_category and error_category not in {"none", "cached", "rate_limited", "timeout", "provider_5xx", "client_4xx"}:
            codes.append("unknown_error_category")
        return _dedupe(codes) or ["route_plan_execution_result_ready"]

    def _checks(
        self,
        readiness: dict[str, Any],
        rows: list[dict[str, Any]],
        forbidden_field_count: int,
    ) -> list[dict[str, Any]]:
        blocked_rows = [row["id"] for row in rows if row["result_status"] == "blocked"]
        review_rows = [row["id"] for row in rows if row["result_status"] == "review_required"]
        missing_route_rows = [row["id"] for row in rows if not row["route_plan_match"]]
        cheap_first_gaps = [row["id"] for row in rows if not row["cheap_first_aligned"]]
        over_limit = len(rows) > int(readiness["manual_run_packet"]["recommended_fixture_limit"])
        return [
            _check(
                "execution-readiness-ready",
                "fail" if readiness["status"] == "blocked" else ("warn" if readiness["status"] != "ready" else "pass"),
                "Execution results must attach to a ready route-plan execution-readiness packet.",
                list(readiness.get("blocking_gate_ids", []))[:12],
            ),
            _check(
                "sanitized-result-metadata-only",
                "fail" if forbidden_field_count else "pass",
                "Submitted result archive input contains only sanitized route observation metadata.",
                [str(forbidden_field_count)] if forbidden_field_count else [],
            ),
            _check(
                "manual-observations-supplied",
                "warn" if not rows else "pass",
                "At least one externally supplied manual result row is needed before this archive is release evidence.",
                [],
            ),
            _check(
                "manual-observations-within-fixture-limit",
                "fail" if over_limit else "pass",
                "Manual result rows stay within the readiness packet fixture_limit=3 low-resource envelope.",
                [str(len(rows))] if over_limit else [],
            ),
            _check(
                "observations-match-route-plan-cases",
                "fail" if missing_route_rows else "pass",
                "Every observed case id maps to the cheap-first legal-document route plan.",
                missing_route_rows,
            ),
            _check(
                "observed-cheap-first-model-alignment",
                "fail" if cheap_first_gaps else "pass",
                "Observed models match the planned precheck or primary cheap-first route for each case.",
                cheap_first_gaps,
            ),
            _check(
                "observation-review-exceptions-visible",
                "warn" if review_rows else "pass",
                "Missing cost, fallback, or latency exceptions remain visible for maintainer review.",
                review_rows,
            ),
            _check(
                "all-result-rows-release-ready",
                "fail" if blocked_rows else ("warn" if review_rows else "pass"),
                "Every archived result row has a release action before use as release evidence.",
                blocked_rows + review_rows,
            ),
            _check(
                "no-provider-side-effects",
                "pass",
                "The archive service does not execute model calls, gateway calls, network calls, config writes, or traffic shifts.",
                [],
            ),
        ]

    def _forbidden_field_count(self, value: Any) -> int:
        return min(50, len(self._forbidden_hits(value)))

    def _forbidden_hits(self, value: Any) -> list[str]:
        hits: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if FORBIDDEN_FIELD_PATTERN.search(str(key)):
                    hits.append("forbidden-field")
                    continue
                hits.extend(self._forbidden_hits(child))
                if len(hits) >= 50:
                    return hits[:50]
        elif isinstance(value, list):
            for child in value[:80]:
                hits.extend(self._forbidden_hits(child))
                if len(hits) >= 50:
                    return hits[:50]
        elif isinstance(value, str) and SENSITIVE_VALUE_PATTERN.search(value[:4096]):
            hits.append("sensitive-value")
        return hits[:50]

    def _status(
        self,
        rows: list[dict[str, Any]],
        blocking_check_ids: list[str],
        warning_check_ids: list[str],
    ) -> str:
        if blocking_check_ids:
            return "blocked"
        if not rows:
            return "not_run"
        if warning_check_ids:
            return "review_required"
        return "ready"

    def _result_status(self, reason_codes: list[str]) -> str:
        blocking = {
            "missing_route_plan_case",
            "observed_case_not_successful",
            "observed_model_missing",
            "observed_model_mismatch",
            "observed_cost_over_route_budget",
            "unknown_error_category",
        }
        if any(code in blocking for code in reason_codes):
            return "blocked"
        review = {"fallback_model_used", "observed_cost_missing", "latency_missing", "latency_over_review_limit"}
        if any(code in review for code in reason_codes):
            return "review_required"
        return "ready"

    def _release_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "accept_as_metadata_only_release_evidence"
        if status == "review_required":
            return "require_maintainer_review_before_release_evidence"
        if "observed_model_mismatch" in reason_codes or "observed_model_missing" in reason_codes:
            return "block_until_observed_model_matches_route_plan"
        if "observed_cost_over_route_budget" in reason_codes:
            return "block_until_cost_metadata_is_under_route_budget"
        return "block_until_route_plan_result_alignment_passes"

    def _next_action(self, status: str, reason_codes: list[str]) -> str:
        if status == "ready":
            return "Attach this row to the route-plan result archive; keep raw prompts and outputs outside source control."
        if status == "review_required":
            return "Review missing cost, fallback, or latency metadata before using this row as release evidence."
        return f"Do not use this row as release evidence until issues are fixed: {', '.join(reason_codes[:6])}."

    def _recommended_actions(
        self,
        status: str,
        rows: list[dict[str, Any]],
        forbidden_field_count: int,
    ) -> list[str]:
        if forbidden_field_count:
            return [
                "Discard raw execution payloads and resubmit only case_id, phase, observed_model, status, token, cost, latency, fallback, and coarse error metadata.",
                "Do not include prompts, legal text, gateway responses, headers, emails, identifiers, credentials, or model output in archive evidence.",
            ]
        if status == "blocked":
            return [
                "Do not attach blocked route-plan execution results to release readiness.",
                "Fix route-plan case matching, observed model alignment, result status, or cost budget blockers first.",
            ]
        if status == "not_run":
            return [
                "Run up to three manual serial legal-document route observations, then submit sanitized metadata to this archive.",
                "Keep max_parallel_model_requests=1 and prefer the planned cheap-first Gemini route for every observed case.",
            ]
        if status == "review_required":
            return [
                "Review missing cost, fallback, and latency observations before treating the archive as release evidence.",
                "Attach the matching execution-readiness packet and maintainer notes outside this metadata-only service.",
            ]
        return [
            "Route-plan execution result metadata is ready as archive-safe release evidence.",
            "Continue archiving only case ids, model ids, token/cost/latency metadata, statuses, and reason codes.",
        ]


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if SENSITIVE_VALUE_PATTERN.search(text):
        return ""
    return re.sub(r"[\r\n\t]+", " ", text)[:180]


def _safe_phase(value: Any) -> str:
    text = _safe_text(value).lower().replace("-", "_")
    return text if text in {"precheck", "primary"} else "primary"


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
        return round(max(0.0, min(float(value), 1000.0)), 8)
    except (TypeError, ValueError):
        return None


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "case"


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
