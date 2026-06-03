from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Iterable


PLAN_ID = "billing-quota-migration-plan-v1"

REQUIRED_SAMPLE_CHECK_TYPES = (
    "schema_contract",
    "forbidden_columns",
    "unique_constraints",
    "idempotency_replay",
    "rollup_reconciliation",
    "rollback_reversibility",
)

ALLOWED_SAMPLE_CHECK_TYPES = REQUIRED_SAMPLE_CHECK_TYPES + (
    "index_plan",
    "retention_policy",
    "data_minimization",
    "batch_accounting",
)

ALLOWED_SAMPLE_CHECK_STATUSES = ("pass", "warn", "fail")

ALLOWED_SAMPLE_CHECK_FIELDS = (
    "check_id",
    "check_type",
    "target",
    "status",
    "blocking",
    "observed_count",
    "expected_count",
    "migration_batch_id",
    "evidence_ref",
    "checked_at",
    "notes",
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
    "database_url",
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
    ("db_connection_uri_like", re.compile(r"\b(postgres(?:ql)?|mysql|mssql|sqlite)://", re.IGNORECASE)),
)


@dataclass(frozen=True)
class ColumnDefinition:
    name: str
    type: str
    nullable: bool
    privacy_classification: str
    notes: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TableDefinition:
    name: str
    purpose: str
    columns: tuple[ColumnDefinition, ...]
    retention: str
    forbidden_columns: tuple[str, ...] = ()

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["columns"] = [column.to_api() for column in self.columns]
        data["forbidden_columns"] = list(self.forbidden_columns)
        return data


@dataclass(frozen=True)
class IndexDefinition:
    name: str
    table: str
    columns: tuple[str, ...]
    unique: bool
    method: str
    purpose: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["columns"] = list(self.columns)
        return data


@dataclass(frozen=True)
class UniqueConstraintDefinition:
    name: str
    table: str
    columns: tuple[str, ...]
    conflict_behavior: str

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)
        data["columns"] = list(self.columns)
        return data


@dataclass(frozen=True)
class MigrationStep:
    order: int
    phase: str
    action: str
    local_only_guard: str
    success_check: str

    def to_api(self) -> dict[str, Any]:
        return asdict(self)


class BillingQuotaMigrationPlanService:
    """Describe and validate a local-only billing quota migration plan.

    This service intentionally performs no database connections, payment calls,
    network requests, router changes, release changes, or ledger updates.
    """

    def build_plan(self, sample_checks: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        check_results = self.validate_sample_checks(sample_checks)
        coverage = self._sample_check_coverage(check_results, sample_checks is None)
        fail_count = sum(1 for item in check_results if item["status"] == "fail")
        warn_count = sum(1 for item in check_results if item["status"] == "warn")

        if sample_checks is None:
            status = "template"
        elif fail_count:
            status = "fail"
        elif warn_count or coverage["missing_required_check_types"]:
            status = "warn"
        else:
            status = "pass"

        tables = self._tables()
        indexes = self._indexes()
        unique_constraints = self._unique_constraints()

        return {
            "status": status,
            "summary": {
                "plan_id": PLAN_ID,
                "checked_sample_count": 0 if sample_checks is None else len(check_results),
                "passing_sample_count": sum(1 for item in check_results if item["status"] == "pass"),
                "warning_sample_count": warn_count,
                "failing_sample_count": fail_count,
                "target_table_count": len(tables),
                "index_count": len(indexes),
                "unique_constraint_count": len(unique_constraints),
                "required_sample_check_type_count": len(REQUIRED_SAMPLE_CHECK_TYPES),
                "target_migration_required_before_durable_quota_storage": True,
                "actual_database_migration_executed": False,
                "database_connection_required": False,
                "payment_integration_required": False,
                "network_required": False,
                "router_changes_allowed": False,
                "release_changes_allowed": False,
                "ledger_changes_allowed": False,
                "raw_payload_storage_allowed": False,
            },
            "tables": [table.to_api() for table in tables],
            "indexes": [index.to_api() for index in indexes],
            "unique_constraints": [constraint.to_api() for constraint in unique_constraints],
            "idempotency": self._idempotency_plan(),
            "replay_steps": [step.to_api() for step in self._replay_steps()],
            "rollback_plan": self._rollback_plan(),
            "data_minimization": self._data_minimization(),
            "forbidden_fields": list(FORBIDDEN_FIELD_PATTERNS),
            "sample_migration_checks": {
                "contract": self._sample_check_contract(),
                "coverage": coverage,
                "checks": check_results or self._template_checks(),
            },
            "recommended_actions": self._recommended_actions(status, check_results, coverage),
            "validation_commands": [
                "python -m pytest tests/test_billing_quota_migration_plan.py -q",
                "python -m compileall services/billing_quota_migration_plan.py tests/test_billing_quota_migration_plan.py",
            ],
        }

    def build_policy(self, sample_checks: Iterable[dict[str, Any]] | None = None) -> dict[str, Any]:
        return self.build_plan(sample_checks)

    def validate_sample_checks(self, sample_checks: Iterable[dict[str, Any]] | None) -> list[dict[str, Any]]:
        if sample_checks is None:
            return []

        results: list[dict[str, Any]] = []
        for index, check in enumerate(sample_checks, start=1):
            if not isinstance(check, dict):
                results.append(self._non_object_check(index))
            else:
                results.append(self._check_sample(index, check))
        return results

    def _tables(self) -> tuple[TableDefinition, ...]:
        return (
            TableDefinition(
                name="billing_quota_migration_batches",
                purpose="Track local migration batches without storing connection strings or payment artifacts.",
                columns=(
                    _column("id", "uuid", False, "local_identifier", "Local generated batch row identifier."),
                    _column("batch_key", "string", False, "opaque_replay_control", "Deterministic local batch key."),
                    _column("plan_version", "string", False, "non_content_metadata", "Migration plan version."),
                    _column("status", "string", False, "non_content_metadata", "planned, replaying, verified, rolled_back, or failed."),
                    _column("source_dataset_hash", "string", False, "opaque_replay_control", "Hash of sanitized source counter set."),
                    _column("started_at", "timestamp", False, "non_content_metadata", "Local dry-run or migration start time."),
                    _column("finished_at", "timestamp", True, "non_content_metadata", "Completion time when available."),
                    _column("created_by_component", "string", False, "non_content_metadata", "Local component name, not an operator identity."),
                ),
                retention="Keep 400 days after final verification or rollback.",
            ),
            TableDefinition(
                name="billing_quota_usage_counters",
                purpose="Persist sanitized quota usage counter events as the migration target fact table.",
                columns=(
                    _column("id", "uuid", False, "local_identifier", "Local generated counter row identifier."),
                    _column("migration_batch_id", "uuid", False, "local_identifier", "Reference to local migration batch."),
                    _column("source_event_hash", "string", False, "opaque_replay_control", "Hash of the sanitized source event."),
                    _column("idempotency_key", "string", False, "opaque_replay_control", "Replay-safe counter key from the quota policy event."),
                    _column("quota_subject_hash", "string", False, "opaque_pseudonymous", "Opaque subject hash only."),
                    _column("subject_type", "string", True, "non_content_metadata", "Coarse subject type."),
                    _column("plan_type", "string", False, "non_content_metadata", "Normalized local plan label."),
                    _column("subscription_status", "string", True, "non_content_metadata", "Coarse entitlement status."),
                    _column("action", "string", False, "non_content_metadata", "Quota action label."),
                    _column("usage_metric", "string", False, "counter", "Counter metric name."),
                    _column("units", "integer", False, "counter", "Positive units applied."),
                    _column("request_units", "integer", True, "counter", "Requested units before decision."),
                    _column("quota_window", "string", False, "non_content_metadata", "Window such as 2026-06."),
                    _column("counter_bucket", "string", False, "non_content_metadata", "Source aggregation bucket."),
                    _column("bucket_start", "timestamp", True, "non_content_metadata", "UTC bucket start."),
                    _column("bucket_end", "timestamp", True, "non_content_metadata", "UTC bucket end."),
                    _column("allowed", "boolean", False, "canonical_policy_metadata", "Decision allowed flag."),
                    _column("decision_status", "string", False, "canonical_policy_metadata", "Canonical decision status."),
                    _column("limit_snapshot", "number", True, "counter", "Limit at decision time."),
                    _column("used_before", "number", True, "counter", "Counter before decision."),
                    _column("remaining_before", "number", True, "counter", "Remaining before decision."),
                    _column("remaining_after", "number", True, "counter", "Remaining after decision."),
                    _column("over_limit_reason_codes", "json_array[string]", True, "canonical_policy_metadata", "Canonical reason codes only."),
                    _column("policy_version", "string", True, "non_content_metadata", "Quota policy version."),
                    _column("entitlement_snapshot_id", "string", True, "opaque_reference", "Opaque entitlement snapshot reference."),
                    _column("source_component", "string", True, "non_content_metadata", "Local emitting component."),
                    _column("trace_ref_hash", "string", True, "opaque_reference", "Opaque trace reference hash."),
                    _column("occurred_at", "timestamp", False, "non_content_metadata", "Counter event time."),
                    _column("created_at", "timestamp", False, "non_content_metadata", "Target row creation time."),
                    _column("migrated_at", "timestamp", False, "non_content_metadata", "Migration write time."),
                ),
                retention="400 days after quota_window closes, then aggregate-only retention.",
            ),
            TableDefinition(
                name="billing_quota_over_limit_reasons",
                purpose="Normalize blocked decision reason codes without storing free-text messages.",
                columns=(
                    _column("id", "uuid", False, "local_identifier", "Local generated reason row identifier."),
                    _column("usage_counter_id", "uuid", False, "local_identifier", "Counter event reference."),
                    _column("reason_code", "string", False, "canonical_policy_metadata", "Canonical reason code."),
                    _column("usage_metric", "string", False, "counter", "Metric that was blocked."),
                    _column("limit_snapshot", "number", True, "counter", "Limit at block time."),
                    _column("used_snapshot", "number", True, "counter", "Used value at block time."),
                    _column("requested_units", "integer", True, "counter", "Requested units at block time."),
                    _column("remaining_snapshot", "number", True, "counter", "Remaining value at block time."),
                    _column("quota_window", "string", False, "non_content_metadata", "Window such as 2026-06."),
                    _column("blocked_at", "timestamp", False, "non_content_metadata", "Block timestamp."),
                ),
                retention="400 days after quota_window closes.",
            ),
            TableDefinition(
                name="billing_quota_subject_monthly_rollups",
                purpose="Support per-subject monthly quota reads from opaque subject hashes.",
                columns=(
                    _column("id", "uuid", False, "local_identifier", "Local generated rollup row identifier."),
                    _column("quota_subject_hash", "string", False, "opaque_pseudonymous", "Opaque subject hash only."),
                    _column("plan_type", "string", False, "non_content_metadata", "Normalized local plan label."),
                    _column("usage_metric", "string", False, "counter", "Counter metric name."),
                    _column("quota_window", "string", False, "non_content_metadata", "Window such as 2026-06."),
                    _column("units_sum", "integer", False, "counter", "Total units counted."),
                    _column("request_count", "integer", False, "counter", "Number of requests."),
                    _column("allowed_count", "integer", False, "counter", "Allowed decisions."),
                    _column("blocked_count", "integer", False, "counter", "Blocked decisions."),
                    _column("last_remaining_after", "number", True, "counter", "Last remaining value."),
                    _column("updated_at", "timestamp", False, "non_content_metadata", "Last rollup update."),
                ),
                retention="400 days after quota_window closes.",
            ),
            TableDefinition(
                name="billing_quota_plan_action_daily_rollups",
                purpose="Support aggregate reporting without subject-level values.",
                columns=(
                    _column("id", "uuid", False, "local_identifier", "Local generated rollup row identifier."),
                    _column("bucket_date", "date", False, "non_content_metadata", "UTC day."),
                    _column("plan_type", "string", False, "non_content_metadata", "Normalized local plan label."),
                    _column("action", "string", False, "non_content_metadata", "Quota action label."),
                    _column("usage_metric", "string", False, "counter", "Counter metric name."),
                    _column("allowed", "boolean", False, "canonical_policy_metadata", "Allowed or blocked decision."),
                    _column("event_count", "integer", False, "counter", "Number of events."),
                    _column("units_sum", "integer", False, "counter", "Total units."),
                    _column("unique_subject_hash_count", "integer", False, "aggregate_only", "Approximate or exact unique opaque subject count."),
                    _column("updated_at", "timestamp", False, "non_content_metadata", "Last rollup update."),
                ),
                retention="400 days.",
            ),
            TableDefinition(
                name="billing_quota_over_limit_reason_daily_rollups",
                purpose="Track aggregate blocked reasons without free text or subject identifiers.",
                columns=(
                    _column("id", "uuid", False, "local_identifier", "Local generated rollup row identifier."),
                    _column("bucket_date", "date", False, "non_content_metadata", "UTC day."),
                    _column("plan_type", "string", False, "non_content_metadata", "Normalized local plan label."),
                    _column("action", "string", False, "non_content_metadata", "Quota action label."),
                    _column("usage_metric", "string", False, "counter", "Counter metric name."),
                    _column("reason_code", "string", False, "canonical_policy_metadata", "Canonical reason code."),
                    _column("blocked_count", "integer", False, "counter", "Blocked count."),
                    _column("requested_units_sum", "integer", False, "counter", "Requested units sum."),
                    _column("remaining_at_block_sum", "number", True, "counter", "Remaining values sum."),
                    _column("updated_at", "timestamp", False, "non_content_metadata", "Last rollup update."),
                ),
                retention="400 days.",
            ),
            TableDefinition(
                name="billing_quota_idempotency_keys",
                purpose="Replay ledger for quota counter migration keys, not a payment ledger.",
                columns=(
                    _column("id", "uuid", False, "local_identifier", "Local generated dedup row identifier."),
                    _column("idempotency_key", "string", False, "opaque_replay_control", "Deterministic opaque counter key."),
                    _column("source_event_hash", "string", False, "opaque_replay_control", "Sanitized source event hash."),
                    _column("migration_batch_id", "uuid", False, "local_identifier", "Batch that first wrote the key."),
                    _column("quota_window", "string", False, "non_content_metadata", "Window such as 2026-06."),
                    _column("usage_metric", "string", False, "counter", "Counter metric name."),
                    _column("first_seen_at", "timestamp", False, "non_content_metadata", "First replay time."),
                    _column("last_seen_at", "timestamp", False, "non_content_metadata", "Most recent replay time."),
                    _column("seen_count", "integer", False, "counter", "Replay count for diagnostics."),
                ),
                retention="45 days after quota_window closes.",
            ),
        )

    def _indexes(self) -> tuple[IndexDefinition, ...]:
        return (
            IndexDefinition(
                name="ix_bq_usage_subject_metric_window",
                table="billing_quota_usage_counters",
                columns=("quota_subject_hash", "usage_metric", "quota_window"),
                unique=False,
                method="btree",
                purpose="Serve monthly per-subject quota lookups.",
            ),
            IndexDefinition(
                name="ix_bq_usage_plan_metric_window_allowed",
                table="billing_quota_usage_counters",
                columns=("plan_type", "usage_metric", "quota_window", "allowed"),
                unique=False,
                method="btree",
                purpose="Support aggregate reconciliation and reporting.",
            ),
            IndexDefinition(
                name="ix_bq_usage_batch",
                table="billing_quota_usage_counters",
                columns=("migration_batch_id", "migrated_at"),
                unique=False,
                method="btree",
                purpose="Enable batch verification and rollback by migrated rows.",
            ),
            IndexDefinition(
                name="ix_bq_reason_counter",
                table="billing_quota_over_limit_reasons",
                columns=("usage_counter_id", "reason_code"),
                unique=False,
                method="btree",
                purpose="Join normalized reason codes to migrated counter rows.",
            ),
            IndexDefinition(
                name="ix_bq_subject_rollup_window",
                table="billing_quota_subject_monthly_rollups",
                columns=("quota_subject_hash", "quota_window"),
                unique=False,
                method="btree",
                purpose="Read all metrics for one subject and window.",
            ),
            IndexDefinition(
                name="ix_bq_plan_action_daily_date",
                table="billing_quota_plan_action_daily_rollups",
                columns=("bucket_date", "plan_type", "usage_metric"),
                unique=False,
                method="btree",
                purpose="Read aggregate quota trends.",
            ),
            IndexDefinition(
                name="ix_bq_reason_daily_date",
                table="billing_quota_over_limit_reason_daily_rollups",
                columns=("bucket_date", "reason_code", "usage_metric"),
                unique=False,
                method="btree",
                purpose="Read blocked reason trends.",
            ),
            IndexDefinition(
                name="ix_bq_dedup_window_metric",
                table="billing_quota_idempotency_keys",
                columns=("quota_window", "usage_metric", "last_seen_at"),
                unique=False,
                method="btree",
                purpose="Expire replay keys after the configured dedup window.",
            ),
        )

    def _unique_constraints(self) -> tuple[UniqueConstraintDefinition, ...]:
        return (
            UniqueConstraintDefinition(
                name="uq_bq_batches_batch_key",
                table="billing_quota_migration_batches",
                columns=("batch_key",),
                conflict_behavior="same batch key resumes the same local replay batch",
            ),
            UniqueConstraintDefinition(
                name="uq_bq_usage_idempotency_key",
                table="billing_quota_usage_counters",
                columns=("idempotency_key",),
                conflict_behavior="same key is a no-op when source_event_hash and counter delta match",
            ),
            UniqueConstraintDefinition(
                name="uq_bq_usage_source_event_hash",
                table="billing_quota_usage_counters",
                columns=("source_event_hash",),
                conflict_behavior="same sanitized source event is migrated at most once",
            ),
            UniqueConstraintDefinition(
                name="uq_bq_reason_per_counter",
                table="billing_quota_over_limit_reasons",
                columns=("usage_counter_id", "reason_code", "usage_metric"),
                conflict_behavior="same reason code for the same counter row is not duplicated",
            ),
            UniqueConstraintDefinition(
                name="uq_bq_subject_monthly_metric",
                table="billing_quota_subject_monthly_rollups",
                columns=("quota_subject_hash", "usage_metric", "quota_window"),
                conflict_behavior="upsert additive deltas into one monthly subject metric row",
            ),
            UniqueConstraintDefinition(
                name="uq_bq_plan_action_daily",
                table="billing_quota_plan_action_daily_rollups",
                columns=("bucket_date", "plan_type", "action", "usage_metric", "allowed"),
                conflict_behavior="upsert aggregate daily counters",
            ),
            UniqueConstraintDefinition(
                name="uq_bq_reason_daily",
                table="billing_quota_over_limit_reason_daily_rollups",
                columns=("bucket_date", "plan_type", "action", "usage_metric", "reason_code"),
                conflict_behavior="upsert aggregate blocked reason counters",
            ),
            UniqueConstraintDefinition(
                name="uq_bq_dedup_idempotency_key",
                table="billing_quota_idempotency_keys",
                columns=("idempotency_key",),
                conflict_behavior="record first writer and ignore exact replay duplicates",
            ),
        )

    def _idempotency_plan(self) -> dict[str, Any]:
        return {
            "required": True,
            "source_event_key": "reuse sanitized billing_quota_usage_counter.idempotency_key when available",
            "migration_batch_key_format": "bqmp:v1:{source_dataset_hash}:{plan_version}:{batch_started_day}",
            "counter_event_hash": "sha256 of canonical sanitized counter fields only",
            "dedup_table": "billing_quota_idempotency_keys",
            "dedup_unique_constraint": "uq_bq_dedup_idempotency_key",
            "collision_behavior": {
                "same_key_same_hash": "no_op_and_increment_seen_count",
                "same_key_different_hash": "quarantine_batch_and_do_not_update_rollups",
                "same_hash_different_key": "reject_until_source_event_is_reconciled",
            },
            "replay_window": "45 days after quota_window closes",
            "forbidden_key_material": [
                "user_id",
                "email",
                "client identifiers",
                "file names",
                "order IDs",
                "payment provider IDs",
                "raw prompts or document text",
            ],
        }

    def _replay_steps(self) -> tuple[MigrationStep, ...]:
        return (
            MigrationStep(
                order=1,
                phase="preflight",
                action="Load only sanitized quota counter exports and reject any field matching forbidden patterns.",
                local_only_guard="Do not open database connections or payment provider clients inside this service.",
                success_check="schema_contract and forbidden_columns sample checks pass.",
            ),
            MigrationStep(
                order=2,
                phase="batch_start",
                action="Create or resume a local migration batch by deterministic batch_key.",
                local_only_guard="The plan defines the batch contract only; later migration code owns execution.",
                success_check="batch_key maps to one batch row through uq_bq_batches_batch_key.",
            ),
            MigrationStep(
                order=3,
                phase="dedup",
                action="Canonicalize each sanitized event, compute source_event_hash, and upsert idempotency_key.",
                local_only_guard="No raw event payload or direct subject identifier is stored with the key.",
                success_check="same idempotency_key cannot apply a second counter delta.",
            ),
            MigrationStep(
                order=4,
                phase="counter_write",
                action="Insert billing_quota_usage_counters rows only after dedup succeeds.",
                local_only_guard="Persist numeric snapshots, canonical codes, opaque hashes, and local metadata only.",
                success_check="uq_bq_usage_idempotency_key and uq_bq_usage_source_event_hash hold.",
            ),
            MigrationStep(
                order=5,
                phase="rollup",
                action="Apply additive deltas to subject monthly, plan action daily, and over-limit reason daily rollups.",
                local_only_guard="Rollups are derived from sanitized counter rows, not source payloads.",
                success_check="rollup_reconciliation sample check matches source sanitized counts.",
            ),
            MigrationStep(
                order=6,
                phase="verify",
                action="Run sample migration checks for schema, uniqueness, replay, reconciliation, and rollback.",
                local_only_guard="Do not enable application reads from target tables in this planning slice.",
                success_check="All required sample check types are present and pass.",
            ),
        )

    def _rollback_plan(self) -> dict[str, Any]:
        return {
            "strategy": "batch-scoped reversible migration with no router, release, ledger, payment, or live DB action in this service",
            "rollback_safe_until": "before application read path is switched to the migrated quota store",
            "steps": [
                "Mark the migration batch as rollback_requested and stop new replay attempts for that batch_key.",
                "Use migration_batch_id to identify target counter rows and reason rows written by the batch.",
                "Subtract the batch deltas from monthly and daily rollups using the same idempotency keys.",
                "Delete or tombstone idempotency keys for the batch only after rollup deltas balance to zero.",
                "Mark the batch rolled_back with observed_count, expected_count, and checked_at metadata.",
                "Keep only aggregate rollback evidence; do not persist rejected raw payloads.",
            ],
            "verification_checks": [
                "batch_accounting",
                "rollup_reconciliation",
                "idempotency_replay",
                "rollback_reversibility",
            ],
            "non_goals": [
                "No payment refund or invoice mutation.",
                "No router or release toggle change.",
                "No continuous update ledger mutation.",
                "No direct database execution from this service.",
            ],
        }

    def _data_minimization(self) -> dict[str, Any]:
        return {
            "allowed_categories": [
                "opaque subject hashes",
                "quota windows",
                "plan and action categories",
                "numeric quota counters",
                "canonical decision statuses",
                "canonical over-limit reason codes",
                "opaque trace and entitlement references",
                "idempotency and migration batch keys",
            ],
            "forbidden_categories": [
                "direct user, organization, client, or contact identifiers",
                "legal document text or generated document text",
                "prompts, messages, raw request bodies, and raw response bodies",
                "file names and uploaded file metadata that can identify a matter",
                "payment provider objects, checkout sessions, invoices, receipts, cards, and customer IDs",
                "credentials, tokens, headers, connection strings, and secrets",
            ],
            "raw_payload_policy": "Raw source payloads are never migration targets and failing samples are rejected without echoing values.",
            "reason_text_policy": "Store canonical reason codes and numeric snapshots only; render messages outside persistence.",
            "subject_policy": "quota_subject_hash is required; user_id, organization_id, email, and client fields are forbidden.",
        }

    def _sample_check_contract(self) -> dict[str, Any]:
        return {
            "required_fields": ["check_id", "check_type", "target", "status"],
            "allowed_fields": list(ALLOWED_SAMPLE_CHECK_FIELDS),
            "allowed_statuses": list(ALLOWED_SAMPLE_CHECK_STATUSES),
            "allowed_check_types": list(ALLOWED_SAMPLE_CHECK_TYPES),
            "required_check_types_before_execution": list(REQUIRED_SAMPLE_CHECK_TYPES),
            "notes": [
                "Sample checks are dry-run evidence objects supplied to this local service.",
                "The service validates check shape and privacy only; it does not query a database.",
                "Evidence refs must be opaque local references, not file names, URLs, credentials, or raw payload snippets.",
            ],
        }

    def _template_checks(self) -> list[dict[str, Any]]:
        return [
            {
                "check_id": "billing-quota-migration-template",
                "status": "pass",
                "event_index": None,
                "blocking": False,
                "warnings": [],
                "failures": [],
                "notes": [
                    "No sample migration checks were supplied.",
                    "Run build_plan(sample_checks) with dry-run checks before implementing an actual migration.",
                ],
            }
        ]

    def _non_object_check(self, index: int) -> dict[str, Any]:
        return {
            "check_id": f"billing-quota-migration-check-{index}",
            "status": "fail",
            "event_index": index,
            "blocking": True,
            "missing_required_fields": ["check_id", "check_type", "target", "status"],
            "unknown_fields": [],
            "forbidden_fields_present": [],
            "sensitive_value_findings": [],
            "warnings": [],
            "failures": ["sample_check_must_be_object"],
            "allowed_to_use_as_evidence": False,
        }

    def _check_sample(self, index: int, check: dict[str, Any]) -> dict[str, Any]:
        missing_required = [
            field
            for field in ("check_id", "check_type", "target", "status")
            if not _has_value(check.get(field))
        ]
        unknown_fields = sorted(set(check) - set(ALLOWED_SAMPLE_CHECK_FIELDS))
        forbidden_fields = [
            field
            for field in sorted(check)
            if self._matches_forbidden_field(field)
        ]
        sensitive_value_findings = self._sensitive_value_findings(check)

        failures: list[str] = []
        warnings: list[str] = []

        if missing_required:
            failures.append("missing_required_fields")
        if forbidden_fields:
            failures.append("forbidden_fields_present")
        if sensitive_value_findings:
            failures.append("sensitive_values_present")

        check_type = check.get("check_type")
        if _has_value(check_type) and check_type not in ALLOWED_SAMPLE_CHECK_TYPES:
            warnings.append("unknown_check_type")

        check_status = check.get("status")
        if _has_value(check_status) and check_status not in ALLOWED_SAMPLE_CHECK_STATUSES:
            failures.append("invalid_sample_check_status")
        elif check_status == "fail":
            failures.append("sample_check_reported_failure")
        elif check_status == "warn":
            warnings.append("sample_check_reported_warning")

        if check.get("blocking") is True and check_status != "pass":
            failures.append("blocking_sample_check_not_passed")
        if unknown_fields:
            warnings.append("unknown_fields_not_in_contract")

        status = "fail" if failures else ("warn" if warnings else "pass")
        return {
            "check_id": str(check.get("check_id") or f"billing-quota-migration-check-{index}"),
            "status": status,
            "event_index": index,
            "blocking": bool(failures),
            "check_type": check.get("check_type"),
            "target": check.get("target"),
            "missing_required_fields": missing_required,
            "unknown_fields": unknown_fields,
            "forbidden_fields_present": forbidden_fields,
            "sensitive_value_findings": sensitive_value_findings,
            "warnings": warnings,
            "failures": failures,
            "allowed_to_use_as_evidence": status != "fail",
        }

    def _sample_check_coverage(self, checks: list[dict[str, Any]], template: bool) -> dict[str, Any]:
        observed = sorted(
            {
                str(check["check_type"])
                for check in checks
                if _has_value(check.get("check_type")) and check.get("check_type") in ALLOWED_SAMPLE_CHECK_TYPES
            }
        )
        missing = [] if template else [item for item in REQUIRED_SAMPLE_CHECK_TYPES if item not in observed]
        return {
            "required_check_types": list(REQUIRED_SAMPLE_CHECK_TYPES),
            "observed_check_types": observed,
            "missing_required_check_types": missing,
            "complete": not missing,
        }

    def _recommended_actions(
        self,
        status: str,
        checks: list[dict[str, Any]],
        coverage: dict[str, Any],
    ) -> list[str]:
        if status == "template":
            return [
                "Review table, index, uniqueness, replay, rollback, and data minimization contracts before writing migrations.",
                "Provide dry-run sample migration checks before any actual durable quota migration is implemented.",
            ]

        actions: list[str] = []
        failing = [item for item in checks if item["status"] == "fail"]
        warning = [item for item in checks if item["status"] == "warn"]
        if failing:
            actions.append("Reject failing sample checks and remove forbidden fields, sensitive values, or failed dry-run evidence.")
        if any(item["sensitive_value_findings"] or item["forbidden_fields_present"] for item in failing):
            actions.append("Replace raw payload, payment, credential, and direct identity data with opaque hashes or aggregate counters.")
        if coverage["missing_required_check_types"]:
            actions.append("Add required dry-run checks for every migration gate before execution.")
        if warning:
            actions.append("Resolve warnings or document why non-blocking sample check warnings are acceptable.")
        if not actions:
            actions.append("Use the migration plan as implementation input; this service still does not execute database changes.")
        return actions

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


def _column(
    name: str,
    column_type: str,
    nullable: bool,
    privacy_classification: str,
    notes: str,
) -> ColumnDefinition:
    return ColumnDefinition(
        name=name,
        type=column_type,
        nullable=nullable,
        privacy_classification=privacy_classification,
        notes=notes,
    )


def _normalize_field(field_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", field_name.lower()).strip("_")


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True
