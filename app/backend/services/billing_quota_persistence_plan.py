from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable


BILLING_QUOTA_EVENT_TYPE = "billing_quota_usage_counter"
PLAN_ID = "billing-quota-persistence-plan-v1"

REQUIRED_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "idempotency_key",
    "quota_subject_hash",
    "plan_type",
    "action",
    "usage_metric",
    "units",
    "quota_window",
    "counter_bucket",
    "allowed",
    "decision_status",
)

RECOMMENDED_FIELDS = (
    "policy_version",
    "entitlement_snapshot_id",
    "source_component",
    "request_units",
    "limit",
    "used_before",
    "remaining_before",
    "remaining_after",
    "over_limit_reason_codes",
)

ALLOWED_FIELDS = (
    "event_id",
    "event_type",
    "timestamp",
    "idempotency_key",
    "quota_subject_hash",
    "subject_type",
    "plan_type",
    "subscription_status",
    "action",
    "usage_metric",
    "units",
    "request_units",
    "quota_window",
    "counter_bucket",
    "bucket_start",
    "bucket_end",
    "allowed",
    "decision_status",
    "limit",
    "used_before",
    "remaining_before",
    "remaining_after",
    "over_limit_reason_codes",
    "over_limit_reasons",
    "policy_version",
    "entitlement_snapshot_id",
    "source_component",
    "trace_ref_hash",
    "created_at",
)

OVER_LIMIT_REASON_ALLOWED_FIELDS = (
    "code",
    "metric",
    "limit",
    "used",
    "requested",
    "remaining",
    "quota_window",
    "policy_version",
    "blocked_at",
    "source_component",
)

FORBIDDEN_FIELD_PATTERNS = (
    "access_token",
    "api_key",
    "authorization",
    "bearer_token",
    "card",
    "checkout_session",
    "client_email",
    "client_info",
    "client_name",
    "client_phone",
    "contact",
    "contract_text",
    "customer_id",
    "document_text",
    "email",
    "file_name",
    "full_document",
    "headers",
    "invoice",
    "legal_text",
    "message",
    "order_id",
    "password",
    "payment",
    "payment_intent",
    "phone",
    "prompt",
    "raw",
    "receipt",
    "refresh_token",
    "request_body",
    "response_body",
    "secret",
    "session_token",
    "stripe",
    "subscription_id",
    "user_email",
    "user_id",
)

SENSITIVE_VALUE_PATTERNS = (
    ("api_key_like", re.compile(r"\bs[k]-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE)),
    ("bearer_token_like", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{12,}\b", re.IGNORECASE)),
    ("email_like", re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b")),
    (
        "payment_provider_id_like",
        re.compile(r"\b(cs_(test|live)|pi|cus|sub|in)_[A-Za-z0-9_]{8,}\b", re.IGNORECASE),
    ),
    ("credential_marker", re.compile(r"\b(password|secret|api[_-]?key|authorization)\b", re.IGNORECASE)),
)

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^bqp:v1:[A-Za-z0-9:_-]{12,180}$")
QUOTA_SUBJECT_HASH_PATTERN = re.compile(r"^qsh_[A-Za-z0-9_-]{16,128}$")

POSITIVE_INTEGER_FIELDS = {"units", "request_units"}
NON_NEGATIVE_NUMBER_FIELDS = {
    "limit",
    "used_before",
    "remaining_before",
    "remaining_after",
}


@dataclass(frozen=True)
class UsageCounterFieldRule:
    name: str
    type: str
    required: bool
    allowed: bool
    privacy_classification: str
    description: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class BillingQuotaPersistencePlanService:
    """Plan safe local persistence for billing quota counters.

    The service is intentionally descriptive and validating only. It performs
    no database writes, payment calls, network calls, or quota consumption.
    """

    def build_plan(self, events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        event_checks = self.validate_sample_events(events)
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
                "plan_id": PLAN_ID,
                "checked_event_count": 0 if events is None else len(event_checks),
                "passing_event_count": sum(1 for item in event_checks if item["status"] == "pass"),
                "warning_event_count": warn_count,
                "failing_event_count": fail_count,
                "allowed_field_count": len(ALLOWED_FIELDS),
                "required_field_count": len(REQUIRED_FIELDS),
                "forbidden_field_pattern_count": len(FORBIDDEN_FIELD_PATTERNS),
                "raw_payload_storage_allowed": False,
                "database_migration_required": False,
                "payment_integration_required": False,
                "network_required": False,
            },
            "usage_counter_schema": self._usage_counter_schema(),
            "aggregation_buckets": self._aggregation_buckets(),
            "retention_policy": self._retention_policy(),
            "idempotency_key_policy": self._idempotency_key_policy(),
            "persistence_checks": event_checks or self._template_checks(),
            "recommended_actions": self._recommended_actions(status, event_checks),
            "privacy_note": (
                "Billing quota persistence is counter-only. Store opaque subject hashes, quota windows, "
                "plan/action categories, numeric counter states, idempotency keys, and canonical reason codes; "
                "do not persist user IDs, client identities, legal content, prompts, file names, payment provider "
                "objects, credentials, request bodies, or response bodies."
            ),
            "validation_commands": [
                "python -m pytest tests/test_billing_quota_persistence_plan.py -q",
                "python -m compileall services/billing_quota_persistence_plan.py tests/test_billing_quota_persistence_plan.py",
            ],
        }

    def build_policy(self, events: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        return self.build_plan(events)

    def validate_sample_events(self, events: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if events is None:
            return []
        checks: list[dict[str, Any]] = []
        for index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                checks.append(self._non_object_event_check(index))
            else:
                checks.append(self._check_event(index, event))
        return checks

    def _usage_counter_schema(self) -> dict[str, Any]:
        return {
            "event_type": BILLING_QUOTA_EVENT_TYPE,
            "allowed_fields": list(ALLOWED_FIELDS),
            "required_fields": list(REQUIRED_FIELDS),
            "recommended_fields": list(RECOMMENDED_FIELDS),
            "forbidden_field_patterns": list(FORBIDDEN_FIELD_PATTERNS),
            "field_rules": [
                UsageCounterFieldRule(
                    name=field,
                    type=self._field_type(field),
                    required=field in REQUIRED_FIELDS,
                    allowed=True,
                    privacy_classification=self._privacy_classification(field),
                    description=self._field_description(field),
                ).to_api()
                for field in ALLOWED_FIELDS
            ],
            "counter_metrics": [
                "document_uploads",
                "document_storage_mb",
                "review_credits",
                "generated_docs",
                "premium_escalations",
            ],
            "over_limit_reason_persistence": {
                "allowed_fields": list(OVER_LIMIT_REASON_ALLOWED_FIELDS),
                "required_when_blocked": ["code", "metric"],
                "free_text_allowed": False,
                "message_storage_allowed": False,
                "notes": [
                    "Persist canonical reason codes and numeric quota snapshots only.",
                    "Render human-readable messages from code at the API or UI boundary.",
                ],
            },
            "schema_notes": [
                "Persist one sanitized counter event per quota decision or completed consumption.",
                "Use quota_subject_hash instead of user_id, organization_id, email, or client identifiers.",
                "Use idempotency_key for replay-safe local upserts before durable storage is introduced.",
                "Keep payment provider IDs and billing artifacts outside quota counter storage.",
            ],
        }

    def _aggregation_buckets(self) -> list[dict[str, Any]]:
        return [
            {
                "bucket": "subject_metric_monthly",
                "grain": "monthly",
                "dimensions": [
                    "quota_subject_hash",
                    "plan_type",
                    "usage_metric",
                    "quota_window",
                ],
                "metrics": [
                    "units_sum",
                    "request_count",
                    "allowed_count",
                    "blocked_count",
                    "last_remaining_after",
                ],
                "privacy_level": "opaque_subject_hash_only",
            },
            {
                "bucket": "plan_action_daily",
                "grain": "daily",
                "dimensions": ["date", "plan_type", "action", "usage_metric", "allowed"],
                "metrics": ["event_count", "units_sum", "unique_subject_hash_count"],
                "privacy_level": "aggregate_only",
            },
            {
                "bucket": "over_limit_reason_daily",
                "grain": "daily",
                "dimensions": ["date", "plan_type", "action", "usage_metric", "reason_code"],
                "metrics": ["blocked_count", "requested_units_sum", "remaining_at_block_sum"],
                "privacy_level": "aggregate_only",
            },
            {
                "bucket": "idempotency_key_dedup",
                "grain": "event",
                "dimensions": ["idempotency_key", "quota_window", "usage_metric"],
                "metrics": ["first_seen_at", "last_seen_at", "seen_count", "first_event_id"],
                "privacy_level": "opaque_replay_control",
            },
        ]

    def _retention_policy(self) -> dict[str, Any]:
        return {
            "raw_event_retention": {
                "rejected_events": "delete_immediately",
                "passing_sanitized_debug_samples": "up_to_7_days",
                "durable_raw_payload_allowed": False,
            },
            "counter_retention": {
                "subject_metric_monthly": "400_days_after_bucket_end",
                "plan_action_daily": "400_days",
                "over_limit_reason_daily": "400_days",
                "idempotency_key_dedup": "45_days_after_bucket_end",
            },
            "deletion_policy": (
                "Delete rejected or raw debug samples immediately after validation. Keep aggregate counters and "
                "deduplication keys only while they contain opaque hashes and canonical codes."
            ),
            "legal_hold_note": (
                "This plan is not a matter audit log or payment ledger. It must not be used to retain legal content "
                "or payment provider records."
            ),
        }

    def _idempotency_key_policy(self) -> dict[str, Any]:
        return {
            "required": True,
            "format": "bqp:v1:{quota_subject_hash_or_hash}:{quota_window}:{action}:{usage_metric}:{source_event_hash}",
            "regex": IDEMPOTENCY_KEY_PATTERN.pattern,
            "components": [
                "prefix",
                "quota_subject_hash_or_hash",
                "quota_window",
                "action",
                "usage_metric",
                "source_event_hash",
            ],
            "collision_behavior": "same_key_same_counter_delta_no_double_count",
            "replay_window": "45_days_after_bucket_end",
            "privacy_note": "The key must be deterministic but must not embed user IDs, emails, file names, order IDs, or payment IDs.",
        }

    def _template_checks(self) -> list[dict[str, Any]]:
        return [
            {
                "check_id": "billing-quota-persistence-template",
                "status": "pass",
                "event_index": None,
                "blocking": False,
                "warnings": [],
                "failures": [],
                "notes": [
                    "No sample events were supplied.",
                    "Run build_plan(events) with sanitized billing quota samples before enabling durable writes.",
                ],
            }
        ]

    def _non_object_event_check(self, index: int) -> dict[str, Any]:
        return {
            "check_id": f"billing-quota-event-{index}",
            "status": "fail",
            "event_index": index,
            "blocking": True,
            "missing_required_fields": list(REQUIRED_FIELDS),
            "missing_recommended_fields": list(RECOMMENDED_FIELDS),
            "unknown_fields": [],
            "forbidden_fields_present": [],
            "sensitive_value_findings": [],
            "idempotency_key_findings": [],
            "quota_subject_findings": [],
            "counter_value_findings": [],
            "over_limit_reason_findings": [],
            "warnings": [],
            "failures": ["event_must_be_object"],
            "allowed_to_persist": False,
        }

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
        idempotency_key_findings = self._idempotency_key_findings(event)
        quota_subject_findings = self._quota_subject_findings(event)
        counter_value_findings = self._counter_value_findings(event)
        over_limit_reason_findings = self._over_limit_reason_findings(event)

        failures = []
        if missing_required:
            failures.append("missing_required_fields")
        if forbidden_fields:
            failures.append("forbidden_fields_present")
        if sensitive_value_findings:
            failures.append("sensitive_values_present")
        if idempotency_key_findings:
            failures.append("invalid_idempotency_key")
        if quota_subject_findings:
            failures.append("invalid_quota_subject_hash")
        if counter_value_findings:
            failures.append("invalid_counter_values")
        if any(item["severity"] == "fail" for item in over_limit_reason_findings):
            failures.append("invalid_over_limit_reason_persistence")

        warnings = []
        if missing_recommended:
            warnings.append("missing_recommended_fields")
        if unknown_fields:
            warnings.append("unknown_fields_not_in_schema")
        if event.get("event_type") not in (None, BILLING_QUOTA_EVENT_TYPE):
            warnings.append("unexpected_event_type")
        if any(item["severity"] == "warn" for item in over_limit_reason_findings):
            warnings.append("over_limit_reason_warning")

        status = "fail" if failures else ("warn" if warnings else "pass")
        return {
            "check_id": f"billing-quota-event-{index}",
            "status": status,
            "event_index": index,
            "blocking": bool(failures),
            "missing_required_fields": missing_required,
            "missing_recommended_fields": missing_recommended,
            "unknown_fields": unknown_fields,
            "forbidden_fields_present": forbidden_fields,
            "sensitive_value_findings": sensitive_value_findings,
            "idempotency_key_findings": idempotency_key_findings,
            "quota_subject_findings": quota_subject_findings,
            "counter_value_findings": counter_value_findings,
            "over_limit_reason_findings": over_limit_reason_findings,
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
            for item_index, nested in enumerate(value):
                findings.extend(self._sensitive_value_findings(nested, f"{path}[{item_index}]"))
            return findings
        if isinstance(value, str):
            for finding_type, pattern in SENSITIVE_VALUE_PATTERNS:
                if pattern.search(value):
                    findings.append({"path": path, "type": finding_type})
        return findings

    def _idempotency_key_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        value = event.get("idempotency_key")
        if not _has_value(value):
            return []
        if not isinstance(value, str):
            return [{"field": "idempotency_key", "type": "not_a_string"}]
        if not IDEMPOTENCY_KEY_PATTERN.match(value):
            return [{"field": "idempotency_key", "type": "invalid_format"}]
        return []

    def _quota_subject_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        value = event.get("quota_subject_hash")
        if not _has_value(value):
            return []
        if not isinstance(value, str):
            return [{"field": "quota_subject_hash", "type": "not_a_string"}]
        if not QUOTA_SUBJECT_HASH_PATTERN.match(value):
            return [{"field": "quota_subject_hash", "type": "must_be_opaque_hash"}]
        return []

    def _counter_value_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        for field in POSITIVE_INTEGER_FIELDS:
            if field in event and (not isinstance(event[field], int) or isinstance(event[field], bool) or event[field] <= 0):
                findings.append({"field": field, "type": "must_be_positive_integer"})
        for field in NON_NEGATIVE_NUMBER_FIELDS:
            if field in event and (not _is_number(event[field]) or event[field] < 0):
                findings.append({"field": field, "type": "must_be_non_negative_number"})
        if "allowed" in event and not isinstance(event["allowed"], bool):
            findings.append({"field": "allowed", "type": "must_be_boolean"})
        return findings

    def _over_limit_reason_findings(self, event: dict[str, Any]) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        allowed = event.get("allowed")
        reason_codes = _safe_codes(event.get("over_limit_reason_codes"))
        reason_items = event.get("over_limit_reasons")

        if allowed is False and not reason_codes and not reason_items:
            findings.append({"field": "over_limit_reasons", "type": "missing_when_blocked", "severity": "fail"})
            return findings

        if allowed is True and (reason_codes or reason_items):
            findings.append({"field": "over_limit_reasons", "type": "present_on_allowed_event", "severity": "warn"})

        if reason_items is None:
            return findings
        if not isinstance(reason_items, (list, tuple)):
            findings.append({"field": "over_limit_reasons", "type": "must_be_list", "severity": "fail"})
            return findings

        for index, item in enumerate(reason_items):
            if not isinstance(item, dict):
                findings.append({"field": f"over_limit_reasons[{index}]", "type": "must_be_object", "severity": "fail"})
                continue
            unknown_nested = sorted(set(item) - set(OVER_LIMIT_REASON_ALLOWED_FIELDS))
            if unknown_nested:
                findings.append(
                    {
                        "field": f"over_limit_reasons[{index}]",
                        "type": "unapproved_reason_fields",
                        "fields": ",".join(unknown_nested),
                        "severity": "fail",
                    }
                )
            forbidden_nested = [
                field
                for field in sorted(item)
                if self._matches_forbidden_field(field)
            ]
            if forbidden_nested:
                findings.append(
                    {
                        "field": f"over_limit_reasons[{index}]",
                        "type": "forbidden_reason_fields",
                        "fields": ",".join(forbidden_nested),
                        "severity": "fail",
                    }
                )
            if not _has_value(item.get("code")):
                findings.append({"field": f"over_limit_reasons[{index}].code", "type": "missing_code", "severity": "fail"})
            if allowed is False and not _has_value(item.get("metric")):
                findings.append(
                    {"field": f"over_limit_reasons[{index}].metric", "type": "missing_metric", "severity": "fail"}
                )
        return findings

    def _recommended_actions(self, status: str, checks: list[dict[str, Any]]) -> list[str]:
        if status == "template":
            return [
                "Validate sanitized billing quota usage samples before enabling any durable counter sink.",
                "Keep payment provider objects, legal content, prompts, client details, and direct user identifiers outside quota counters.",
            ]

        failing = [item for item in checks if item["status"] == "fail"]
        warning = [item for item in checks if item["status"] == "warn"]
        actions: list[str] = []
        if failing:
            actions.append("Reject failing billing quota events before persistence and remove forbidden or sensitive fields.")
        if any(item["idempotency_key_findings"] for item in failing):
            actions.append("Regenerate idempotency keys using the bqp:v1 opaque deterministic format.")
        if any(item["quota_subject_findings"] for item in failing):
            actions.append("Replace direct subject identifiers with quota_subject_hash values.")
        if any(item["over_limit_reason_findings"] for item in failing):
            actions.append("Persist blocked decisions with canonical reason codes and numeric quota snapshots only.")
        if warning:
            actions.append("Backfill recommended fields for reconciliation, retention enforcement, and aggregate reporting.")
        if not actions:
            actions.append("Persist sanitized counter events with idempotent local upsert semantics.")
        return actions

    def _field_type(self, field: str) -> str:
        if field == "allowed":
            return "boolean"
        if field in {"units", "request_units"}:
            return "integer"
        if field in {"limit", "used_before", "remaining_before", "remaining_after"}:
            return "number"
        if field in {"over_limit_reason_codes"}:
            return "array[string]"
        if field in {"over_limit_reasons"}:
            return "array[object]"
        return "string"

    def _privacy_classification(self, field: str) -> str:
        if field in {"quota_subject_hash", "trace_ref_hash", "idempotency_key"}:
            return "opaque_pseudonymous"
        if field in {"limit", "used_before", "remaining_before", "remaining_after", "units", "request_units"}:
            return "counter"
        if field in {"over_limit_reason_codes", "over_limit_reasons"}:
            return "canonical_policy_metadata"
        return "non_content_metadata"

    def _field_description(self, field: str) -> str:
        descriptions = {
            "event_id": "Stable sanitized counter event identifier.",
            "event_type": f"Must be {BILLING_QUOTA_EVENT_TYPE}.",
            "timestamp": "UTC timestamp for the quota decision or completed quota consumption.",
            "idempotency_key": "Deterministic replay-safe key for local upsert and deduplication.",
            "quota_subject_hash": "Opaque HMAC or stable local hash for the quota subject.",
            "subject_type": "Coarse subject type such as account, organization, or internal.",
            "plan_type": "Normalized product plan label.",
            "subscription_status": "Coarse local entitlement status, not a payment provider object.",
            "action": "Quota action such as review, document_upload, generated_document, or premium_model_escalation.",
            "usage_metric": "Counter metric consumed or checked.",
            "units": "Positive units applied to the usage counter.",
            "request_units": "Positive requested units before policy evaluation.",
            "quota_window": "Quota period such as 2026-06.",
            "counter_bucket": "Aggregation bucket name used by the local quota sink.",
            "bucket_start": "UTC bucket start timestamp or date.",
            "bucket_end": "UTC bucket end timestamp or date.",
            "allowed": "Whether the quota decision allowed the requested action.",
            "decision_status": "Canonical decision status such as ready or blocked.",
            "limit": "Numeric limit snapshot for the metric.",
            "used_before": "Counter value before this decision.",
            "remaining_before": "Remaining counter before this decision.",
            "remaining_after": "Remaining counter after the allowed consumption, or unchanged if blocked.",
            "over_limit_reason_codes": "Canonical blocked reason codes.",
            "over_limit_reasons": "Structured reason objects with canonical code and numeric quota snapshot.",
            "policy_version": "Local policy version that produced the decision.",
            "entitlement_snapshot_id": "Opaque local entitlement snapshot reference.",
            "source_component": "Local component that emitted the event.",
            "trace_ref_hash": "Opaque trace correlation hash.",
            "created_at": "UTC time the sanitized counter event was created.",
        }
        return descriptions.get(field, "Sanitized billing quota counter metadata.")


def _normalize_field(field_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", field_name.lower()).strip("_")


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _safe_codes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raw_codes: Iterable[Any] = (value,)
    else:
        try:
            raw_codes = tuple(value)
        except TypeError:
            raw_codes = (value,)
    return tuple(
        sorted(
            {
                str(code).strip().lower()
                for code in raw_codes
                if str(code).strip()
            }
        )
    )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
