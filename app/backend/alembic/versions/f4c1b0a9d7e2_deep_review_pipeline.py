"""deep review pipeline persistence

Revision ID: f4c1b0a9d7e2
Revises: ea929775f1da
Create Date: 2026-05-14 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c1b0a9d7e2"
down_revision: Union[str, Sequence[str], None] = "ea929775f1da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("extraction_metadata_json", sa.String(), nullable=True))
    op.add_column("documents", sa.Column("extraction_error", sa.String(), nullable=True))

    op.add_column("review_reports", sa.Column("full_report_json", sa.Text(), nullable=True))
    op.add_column("review_reports", sa.Column("pipeline_trace_json", sa.Text(), nullable=True))

    op.add_column("risk_items", sa.Column("risk_id", sa.String(), nullable=True))
    op.add_column("risk_items", sa.Column("risk_type", sa.String(), nullable=True))
    op.add_column("risk_items", sa.Column("clause_location", sa.String(), nullable=True))
    op.add_column("risk_items", sa.Column("issue_location", sa.String(), nullable=True))
    op.add_column("risk_items", sa.Column("legal_analysis_json", sa.Text(), nullable=True))
    op.add_column("risk_items", sa.Column("revision_plan_json", sa.Text(), nullable=True))
    op.add_column("risk_items", sa.Column("citations_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("risk_items", "citations_json")
    op.drop_column("risk_items", "revision_plan_json")
    op.drop_column("risk_items", "legal_analysis_json")
    op.drop_column("risk_items", "issue_location")
    op.drop_column("risk_items", "clause_location")
    op.drop_column("risk_items", "risk_type")
    op.drop_column("risk_items", "risk_id")

    op.drop_column("review_reports", "pipeline_trace_json")
    op.drop_column("review_reports", "full_report_json")

    op.drop_column("documents", "extraction_error")
    op.drop_column("documents", "extraction_metadata_json")
