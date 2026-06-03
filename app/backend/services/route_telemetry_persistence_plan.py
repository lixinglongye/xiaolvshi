from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable


ROUTE_TELEMETRY_EVENT_TYPE = "model_route_decision"

REQUIRED_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "task",
    "resolved_model",
    "success",
)

RECOMMENDED_FIELDS = (
    "route_id",
    "requested_model",
    "inference_source",
    "routed_to_recommended_model",
    "is_over_budget",
    "requires_operator_review",
    "is_known_model",
)

ALLOWED_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "route_id",
    "task",
    "inference_source",
    "requested_model",
    "resolved_model",
    "gateway",
    "provider",
    "routed_to_recommended_model",
    "is_over_budget",
    "requires_operator_review",
    "allow_over_budget_model",
    "is_known_model",
    "estimated_input_tokens",
    "estimated_output_tokens",
    "estimated_cost_usd",
    "latency_ms",
    "success",
    "error_category",
    "stream",
    "cache_hit",
    "http_status",
)

FORBIDDEN_FIELD_PATTERNS = (
    "access_token",
    "api_key",
    "authorization",
    "bearer_token",
    "client_email",
    "client_info",
    "client_name",
    "client_phone",
    "contact",
    "document_text",
    "email",
    "file_name",
    "full_document",
    "headers",
    "message",
    "password",
    "phone",
    "prompt",
    "raw_document",
    "raw_model_output",
    "request_body",
    "response_body",
    "secret",
    "refresh_token",
    "session_token",
    "user_email",
)

SENSITIVE_VALUE_PATTERNS = (
    ("api_key_like", re.compile(r"\bs[k]-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE)),
    ("email_like", re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b")),
    ("credential_marker", re.compile(r"\b(password|secret|api[_-]?key|authorization)\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class TelemetryFieldRule:
    name: str
    type: str
    required: bool
    allowed: bool
    description: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class RouteTelemetryPersistencePlanService:
    """Plan safe persistence for route telemetry without storing prompts or clients."""

    def build_plan(self, events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        normalized_events = [event for event in events or [] if isinstance(event, dict)]
        event_checks = [self._check_event(index, event) for index, event in enumerate(normalized_events, start=1)]
        fail_count = sum(1 for item in event_checks if item["status"] == "fail")
        warn_count = sum(1 for item in event_checks if item["status"] == "warn")

        if events is None:
            status = "template"
        elif fail_count:
            status = "fail"
        elif warn_count:
            status = "warn"
        else:
            status = "pass"

        return {
            "status": status,
            "summary": {
                "plan_id": "route-telemetry-persistence-plan-v1",
                "checked_event_count": len(normalized_events),
                "passing_event_count": sum(1 for item in event_checks if item["status"] == "pass"),
                "warning_event_count": warn_count,
                "failing_event_count": fail_count,
                "allowed_field_count": len(ALLOWED_FIELDS),
                "required_field_count": len(REQUIRED_FIELDS),
                "forbidden_field_pattern_count": len(FORBIDDEN_FIELD_PATTERNS),
                "raw_payload_storage_allowed": False,
                "database_migration_required": False,
            },
            "event_schema": self._event_schema(),
            "retention_policy": self._retention_policy(),
            "persistence_checks": event_checks or self._template_checks(),
            "recommended_actions": self._recommended_actions(status, event_checks),
            "privacy_note": (
                "Route telemetry persistence is metadata-only. Store route decisions, model IDs, task labels, "
                "aggregate counters, and bounded cost or latency metrics; do not persist prompts, messages, "
                "raw legal documents, client contact details, credentials, headers, request bodies, or model outputs."
            ),
            "validation_commands": [
                "python -m pytest tests/test_route_telemetry_persistence_plan.py -q",
                "python -m compileall services/route_telemetry_persistence_plan.py",
            ],
        }

    def build_policy(self, events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        return self.build_plan(events)

    def _event_schema(self) -> dict[str, Any]:
        rules = [
            TelemetryFieldRule(
                name=field,
                type=self._field_type(field),
                required=field in REQUIRED_FIELDS,
                allowed=True,
                description=self._field_description(field),
            ).to_api()
            for field in ALLOWED_FIELDS
        ]
        return {
            "event_type": ROUTE_TELEMETRY_EVENT_TYPE,
            "allowed_fields": list(ALLOWED_FIELDS),
            "required_fields": list(REQUIRED_FIELDS),
            "recommended_fields": list(RECOMMENDED_FIELDS),
            "forbidden_field_patterns": list(FORBIDDEN_FIELD_PATTERNS),
            "field_rules": rules,
            "schema_notes": [
                "Persist one sanitized route-decision event per completed model route.",
                "Use stable IDs or hashes for route and matter references; never duplicate source content.",
                "Keep detailed request and response bodies outside telemetry storage.",
            ],
        }

    def _retention_policy(self) -> dict[str, Any]:
        return {
            "raw_event_retention": {
                "default": "do_not_persist_until_all_checks_pass",
                "after_pass": "up_to_30_days_for_debug_sampling",
                "notes": [
                    "Raw sanitized events are optional and short-lived.",
                    "Failing events should be rejected or redacted before any durable write.",
                ],
            },
            "aggregate_retention": {
                "task_model_daily_counters": "400_days",
                "budget_and_downgrade_counters": "400_days",
                "error_category_daily_counters": "180_days",
                "operator_review_counters": "400_days",
            },
            "aggregation_keys": [
                "date",
                "task",
                "resolved_model",
                "inference_source",
                "routed_to_recommended_model",
                "is_over_budget",
                "requires_operator_review",
                "success",
                "error_category",
            ],
            "rollup_metrics": [
                "request_count",
                "success_count",
                "failure_count",
                "downgrade_count",
                "over_budget_count",
                "operator_review_count",
                "unknown_model_count",
                "estimated_cost_usd_sum",
                "latency_ms_p50",
                "latency_ms_p95",
            ],
            "deletion_policy": (
                "Delete rejected raw samples immediately. Keep aggregated counters because they contain no prompts, "
                "client identifiers, document text, or credentials."
            ),
        }

    def _template_checks(self) -> list[dict[str, Any]]:
        return [
            {
                "check_id": "route-telemetry-schema-template",
                "status": "pass",
                "event_index": None,
                "blocking": False,
                "warnings": [],
                "failures": [],
                "notes": [
                    "No sample events were supplied.",
                    "Use build_plan(events) before enabling durable writes.",
                ],
            }
        ]

    def _check_event(self, index: int, event: dict[str, Any]) -> dict[str, Any]:
        fields = set(event)
        missing_required = [field for field in REQUIRED_FIELDS if not _has_value(event.get(field))]
        missing_recommended = [field for field in RECOMMENDED_FIELDS if not _has_value(event.get(field))]
        unknown_fields = sorted(fields - set(ALLOWED_FIELDS))
        forbidden_fields = [
            field
            for field in sorted(fields)
            if self._matches_forbidden_field(field)
        ]
        sensitive_value_findings = self._sensitive_value_findings(event)
        event_type_warning = []
        if event.get("event_type") not in (None, ROUTE_TELEMETRY_EVENT_TYPE):
            event_type_warning.append("unexpected_event_type")

        failures = []
        if missing_required:
            failures.append("missing_required_fields")
        if forbidden_fields:
            failures.append("forbidden_fields_present")
        if sensitive_value_findings:
            failures.append("sensitive_values_present")

        warnings = []
        if missing_recommended:
            warnings.append("missing_recommended_fields")
        if unknown_fields:
            warnings.append("unknown_fields_not_in_schema")
        warnings.extend(event_type_warning)

        status = "fail" if failures else ("warn" if warnings else "pass")
        return {
            "check_id": f"route-telemetry-event-{index}",
            "status": status,
            "event_index": index,
            "blocking": bool(failures),
            "missing_required_fields": missing_required,
            "missing_recommended_fields": missing_recommended,
            "unknown_fields": unknown_fields,
            "forbidden_fields_present": forbidden_fields,
            "sensitive_value_findings": sensitive_value_findings,
            "warnings": warnings,
            "failures": failures,
            "allowed_to_persist": status != "fail",
        }

    def _matches_forbidden_field(self, field_name: str) -> bool:
        normalized = _normalize_field(field_name)
        return any(pattern in normalized for pattern in FORBIDDEN_FIELD_PATTERNS)

    def _sensitive_value_findings(self, value: Any, path: str = "$") -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        if isinstance(value, dict):
            for key, nested in value.items():
                next_path = f"{path}.{key}"
                if self._matches_forbidden_field(str(key)):
                    findings.append({"path": next_path, "type": "forbidden_nested_field"})
                findings.extend(self._sensitive_value_findings(nested, next_path))
            return findings
        if isinstance(value, (list, tuple, set)):
            for index, nested in enumerate(value):
                findings.extend(self._sensitive_value_findings(nested, f"{path}[{index}]"))
            return findings
        if isinstance(value, str):
            for finding_type, pattern in SENSITIVE_VALUE_PATTERNS:
                if pattern.search(value):
                    findings.append({"path": path, "type": finding_type})
        return findings

    def _recommended_actions(self, status: str, checks: list[dict[str, Any]]) -> list[str]:
        if status == "template":
            return [
                "Run this plan against sanitized route telemetry samples before enabling durable writes.",
                "Keep raw request, response, prompt, and client fields outside the route telemetry sink.",
            ]

        failing = [item for item in checks if item["status"] == "fail"]
        warning = [item for item in checks if item["status"] == "warn"]
        actions: list[str] = []
        if failing:
            actions.append("Reject failing route telemetry events before persistence and remove forbidden or sensitive fields.")
        if any(item["missing_required_fields"] for item in failing):
            actions.append("Populate required route metadata: event_id, event_type, timestamp, task, resolved_model, and success.")
        if any(item["sensitive_value_findings"] or item["forbidden_fields_present"] for item in failing):
            actions.append("Replace prompts, client details, credentials, headers, and raw model output with stable metadata references.")
        if warning:
            actions.append("Backfill recommended route metadata so aggregate reporting can explain downgrades, budget gates, and task inference.")
        if not actions:
            actions.append("Persist sanitized route events and roll them up into daily aggregate counters.")
        return actions

    def _field_type(self, field: str) -> str:
        if field in {
            "routed_to_recommended_model",
            "is_over_budget",
            "requires_operator_review",
            "allow_over_budget_model",
            "is_known_model",
            "success",
            "stream",
            "cache_hit",
        }:
            return "boolean"
        if field in {"estimated_input_tokens", "estimated_output_tokens", "latency_ms", "http_status"}:
            return "integer"
        if field == "estimated_cost_usd":
            return "number"
        return "string"

    def _field_description(self, field: str) -> str:
        descriptions = {
            "event_id": "Stable telemetry event identifier.",
            "event_type": "Must be model_route_decision for route telemetry persistence.",
            "timestamp": "UTC timestamp for the route decision.",
            "route_id": "Internal deterministic route identifier.",
            "task": "Normalized task label such as fast, classification, ocr, review, or pdf.",
            "inference_source": "Whether the task was explicit, inferred, or defaulted.",
            "requested_model": "Model requested by caller after canonicalization.",
            "resolved_model": "Model selected by the runtime router after policy enforcement.",
            "gateway": "Gateway label such as default, newapi, or local proxy.",
            "provider": "Provider family label used for aggregate reporting.",
            "routed_to_recommended_model": "Whether the router downgraded to the recommended cheap-first default.",
            "is_over_budget": "Whether the requested route exceeded configured cost bounds.",
            "requires_operator_review": "Whether routing required human review before expensive or risky execution.",
            "allow_over_budget_model": "Whether an explicit reviewed override allowed the expensive route.",
            "is_known_model": "Whether the model exists in the local catalog.",
            "estimated_input_tokens": "Estimated input token count only, not prompt text.",
            "estimated_output_tokens": "Estimated output token count only, not model output text.",
            "estimated_cost_usd": "Estimated route cost for aggregate budget monitoring.",
            "latency_ms": "Elapsed route or request latency in milliseconds.",
            "success": "Whether the routed model call completed successfully.",
            "error_category": "Coarse sanitized error category, never a stack trace or raw response body.",
            "stream": "Whether the request used streaming.",
            "cache_hit": "Whether a sanitized cache entry satisfied the request.",
            "http_status": "Coarse HTTP status code if one is available.",
        }
        return descriptions.get(field, "Sanitized route telemetry metadata.")


def _normalize_field(field_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", field_name.lower()).strip("_")


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True
