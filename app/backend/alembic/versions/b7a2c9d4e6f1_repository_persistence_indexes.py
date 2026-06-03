"""repository persistence indexes

Revision ID: b7a2c9d4e6f1
Revises: f4c1b0a9d7e2
Create Date: 2026-06-04 04:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7a2c9d4e6f1"
down_revision: Union[str, Sequence[str], None] = "f4c1b0a9d7e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_workbench_section_states",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("case_ref_hash", sa.String(), nullable=False),
        sa.Column("matter_ref_hash", sa.String(), nullable=True),
        sa.Column("section", sa.String(), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=True),
        sa.Column("state_delta_json", sa.JSON(), nullable=False),
        sa.Column("latest_event_id", sa.String(), nullable=True),
        sa.Column("policy_version", sa.String(), nullable=True),
        sa.Column("validation_status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "case_ref_hash",
            "section",
            name="uq_case_workbench_section_state_user_case_section",
        ),
    )
    op.create_index(op.f("ix_case_workbench_section_states_id"), "case_workbench_section_states", ["id"], unique=False)
    op.create_index(op.f("ix_case_workbench_section_states_user_id"), "case_workbench_section_states", ["user_id"], unique=False)
    op.create_index(op.f("ix_case_workbench_section_states_case_ref_hash"), "case_workbench_section_states", ["case_ref_hash"], unique=False)
    op.create_index(op.f("ix_case_workbench_section_states_matter_ref_hash"), "case_workbench_section_states", ["matter_ref_hash"], unique=False)
    op.create_index(op.f("ix_case_workbench_section_states_section"), "case_workbench_section_states", ["section"], unique=False)
    op.create_index("ix_case_workbench_section_states_user_case", "case_workbench_section_states", ["user_id", "case_ref_hash"], unique=False)

    op.create_table(
        "case_workbench_state_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("case_ref_hash", sa.String(), nullable=False),
        sa.Column("section", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("event_hash", sa.String(), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("event_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_case_workbench_state_event_user_event"),
    )
    op.create_index(op.f("ix_case_workbench_state_events_id"), "case_workbench_state_events", ["id"], unique=False)
    op.create_index(op.f("ix_case_workbench_state_events_user_id"), "case_workbench_state_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_case_workbench_state_events_case_ref_hash"), "case_workbench_state_events", ["case_ref_hash"], unique=False)
    op.create_index(op.f("ix_case_workbench_state_events_section"), "case_workbench_state_events", ["section"], unique=False)
    op.create_index(op.f("ix_case_workbench_state_events_event_id"), "case_workbench_state_events", ["event_id"], unique=False)
    op.create_index(op.f("ix_case_workbench_state_events_event_hash"), "case_workbench_state_events", ["event_hash"], unique=False)
    op.create_index(op.f("ix_case_workbench_state_events_state_version"), "case_workbench_state_events", ["state_version"], unique=False)
    op.create_index("ix_case_workbench_state_events_user_case_section", "case_workbench_state_events", ["user_id", "case_ref_hash", "section"], unique=False)

    op.create_table(
        "legal_source_index_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("index_entry_id", sa.String(), nullable=False),
        sa.Column("index_version", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("jurisdiction", sa.String(), nullable=False),
        sa.Column("effective_date", sa.String(), nullable=False),
        sa.Column("citation", sa.String(), nullable=False),
        sa.Column("citation_key", sa.String(), nullable=True),
        sa.Column("dedupe_key", sa.String(), nullable=False),
        sa.Column("freshness_status", sa.String(), nullable=False),
        sa.Column("freshness_expires_at", sa.String(), nullable=False),
        sa.Column("metadata_hash", sa.String(), nullable=False),
        sa.Column("use_case", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_title", sa.String(), nullable=True),
        sa.Column("last_verified_at", sa.String(), nullable=False),
        sa.Column("authority_level", sa.String(), nullable=True),
        sa.Column("issuer", sa.String(), nullable=True),
        sa.Column("publication_date", sa.String(), nullable=True),
        sa.Column("amendment_date", sa.String(), nullable=True),
        sa.Column("official_url", sa.String(), nullable=True),
        sa.Column("retrieval_locator", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("ingestion_batch_id", sa.String(), nullable=True),
        sa.Column("indexed_at", sa.String(), nullable=True),
        sa.Column("retention_bucket", sa.String(), nullable=True),
        sa.Column("effective_title_key", sa.String(), nullable=True),
        sa.Column("content_hash_key", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", name="uq_legal_source_index_entries_source_id"),
        sa.UniqueConstraint("index_entry_id", name="uq_legal_source_index_entries_index_entry_id"),
    )
    for column in (
        "id",
        "source_id",
        "index_entry_id",
        "index_version",
        "source_type",
        "jurisdiction",
        "effective_date",
        "citation",
        "citation_key",
        "dedupe_key",
        "freshness_status",
        "use_case",
        "last_verified_at",
        "authority_level",
        "issuer",
        "retention_bucket",
    ):
        op.create_index(op.f(f"ix_legal_source_index_entries_{column}"), "legal_source_index_entries", [column], unique=False)
    op.create_index("ix_legal_source_index_entries_query", "legal_source_index_entries", ["jurisdiction", "source_type", "freshness_status"], unique=False)

    op.create_table(
        "billing_quota_usage_counters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(length=220), nullable=False),
        sa.Column("source_event_hash", sa.String(length=64), nullable=False),
        sa.Column("quota_subject_hash", sa.String(length=140), nullable=False),
        sa.Column("quota_window", sa.String(length=32), nullable=False),
        sa.Column("usage_metric", sa.String(length=80), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("limit_value", sa.Float(), nullable=True),
        sa.Column("used_value", sa.Float(), nullable=True),
        sa.Column("remaining_value", sa.Float(), nullable=True),
        sa.Column("decision_status", sa.String(length=40), nullable=False),
        sa.Column("reason_codes_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_bq_usage_idempotency_key"),
        sa.UniqueConstraint("source_event_hash", name="uq_bq_usage_source_event_hash"),
    )
    for column in (
        "id",
        "idempotency_key",
        "source_event_hash",
        "quota_subject_hash",
        "quota_window",
        "usage_metric",
        "decision_status",
    ):
        op.create_index(op.f(f"ix_billing_quota_usage_counters_{column}"), "billing_quota_usage_counters", [column], unique=False)

    op.create_table(
        "billing_quota_idempotency_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("idempotency_key", sa.String(length=220), nullable=False),
        sa.Column("source_event_hash", sa.String(length=64), nullable=False),
        sa.Column("quota_subject_hash", sa.String(length=140), nullable=False),
        sa.Column("quota_window", sa.String(length=32), nullable=False),
        sa.Column("usage_metric", sa.String(length=80), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seen_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_bq_dedup_idempotency_key"),
    )
    for column in ("id", "idempotency_key", "quota_subject_hash", "quota_window", "usage_metric"):
        op.create_index(op.f(f"ix_billing_quota_idempotency_keys_{column}"), "billing_quota_idempotency_keys", [column], unique=False)


def downgrade() -> None:
    for column in ("id", "idempotency_key", "quota_subject_hash", "quota_window", "usage_metric"):
        op.drop_index(op.f(f"ix_billing_quota_idempotency_keys_{column}"), table_name="billing_quota_idempotency_keys")
    op.drop_table("billing_quota_idempotency_keys")

    for column in (
        "id",
        "idempotency_key",
        "source_event_hash",
        "quota_subject_hash",
        "quota_window",
        "usage_metric",
        "decision_status",
    ):
        op.drop_index(op.f(f"ix_billing_quota_usage_counters_{column}"), table_name="billing_quota_usage_counters")
    op.drop_table("billing_quota_usage_counters")

    op.drop_index("ix_legal_source_index_entries_query", table_name="legal_source_index_entries")
    for column in (
        "retention_bucket",
        "issuer",
        "authority_level",
        "last_verified_at",
        "use_case",
        "freshness_status",
        "dedupe_key",
        "citation_key",
        "citation",
        "effective_date",
        "jurisdiction",
        "source_type",
        "index_version",
        "index_entry_id",
        "source_id",
        "id",
    ):
        op.drop_index(op.f(f"ix_legal_source_index_entries_{column}"), table_name="legal_source_index_entries")
    op.drop_table("legal_source_index_entries")

    op.drop_index("ix_case_workbench_state_events_user_case_section", table_name="case_workbench_state_events")
    for column in ("state_version", "event_hash", "event_id", "section", "case_ref_hash", "user_id", "id"):
        op.drop_index(op.f(f"ix_case_workbench_state_events_{column}"), table_name="case_workbench_state_events")
    op.drop_table("case_workbench_state_events")

    op.drop_index("ix_case_workbench_section_states_user_case", table_name="case_workbench_section_states")
    for column in ("section", "matter_ref_hash", "case_ref_hash", "user_id", "id"):
        op.drop_index(op.f(f"ix_case_workbench_section_states_{column}"), table_name="case_workbench_section_states")
    op.drop_table("case_workbench_section_states")
