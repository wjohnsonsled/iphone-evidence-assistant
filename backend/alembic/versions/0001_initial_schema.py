"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


CASE_STATUSES = ("created", "processing", "completed", "completed_with_warnings", "failed")
JOB_STATUSES = ("queued", "running", "processing", "completed", "failed")


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("source_path", sa.Text()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(f"status IN {CASE_STATUSES}", name="ck_cases_status"),
    )
    op.create_index("ix_cases_status", "cases", ["status"])

    op.create_table(
        "devices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_name", sa.String(length=255)),
        sa.Column("device_type", sa.String(length=64), nullable=False),
        sa.Column("ios_version", sa.String(length=64)),
        sa.Column("product_type", sa.String(length=128)),
        sa.Column("serial_number", sa.String(length=128)),
        sa.Column("udid", sa.String(length=128)),
        sa.Column("backup_identifier", sa.String(length=255)),
        sa.Column("backup_encrypted", sa.Boolean()),
        sa.Column("backup_created_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_devices_case_id", "devices", ["case_id"])

    op.create_table(
        "evidence_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Uuid(), sa.ForeignKey("devices.id", ondelete="SET NULL")),
        sa.Column("external_event_id", sa.String(length=255)),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=128)),
        sa.Column("timestamp", sa.DateTime(timezone=True)),
        sa.Column("timestamp_end", sa.DateTime(timezone=True)),
        sa.Column("timezone_name", sa.String(length=128)),
        sa.Column("summary", sa.Text()),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_values_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_artifact", sa.String(length=255)),
        sa.Column("source_database", sa.String(length=255)),
        sa.Column("source_table", sa.String(length=255)),
        sa.Column("source_record_id", sa.String(length=255)),
        sa.Column("source_path", sa.Text()),
        sa.Column("parser_name", sa.String(length=128)),
        sa.Column("parser_version", sa.String(length=64)),
        sa.Column("confidence_score", sa.Integer()),
        sa.Column("confidence_basis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("artifact_hash", sa.String(length=128)),
        sa.Column("conversation_key", sa.String(length=255)),
        sa.Column("contact_key", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    for column in ("case_id", "device_id", "timestamp", "event_type", "category", "source_artifact", "conversation_key", "contact_key"):
        op.create_index(f"ix_evidence_events_{column}", "evidence_events", [column])
    op.create_index("ix_evidence_events_external_event_id", "evidence_events", ["external_event_id"])
    op.create_index("ix_evidence_events_artifact_hash", "evidence_events", ["artifact_hash"])
    op.create_index("ix_evidence_events_case_timestamp", "evidence_events", ["case_id", "timestamp"])
    op.create_index("ix_evidence_events_case_event_type", "evidence_events", ["case_id", "event_type"])
    op.create_index("ix_evidence_events_case_conversation_key", "evidence_events", ["case_id", "conversation_key"])

    op.create_table(
        "artifact_coverage",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.Uuid(), sa.ForeignKey("devices.id", ondelete="SET NULL")),
        sa.Column("artifact_name", sa.String(length=255), nullable=False),
        sa.Column("coverage_status", sa.String(length=128), nullable=False),
        sa.Column("parser_name", sa.String(length=128)),
        sa.Column("source_path", sa.Text()),
        sa.Column("records_parsed", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_artifact_coverage_case_id", "artifact_coverage", ["case_id"])
    op.create_index("ix_artifact_coverage_device_id", "artifact_coverage", ["device_id"])
    op.create_index("ix_artifact_coverage_coverage_status", "artifact_coverage", ["coverage_status"])

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("case_id", sa.Uuid(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("stage", sa.String(length=64)),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("warnings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("statistics_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(f"status IN {JOB_STATUSES}", name="ck_processing_jobs_status"),
    )
    op.create_index("ix_processing_jobs_case_id", "processing_jobs", ["case_id"])


def downgrade() -> None:
    op.drop_table("processing_jobs")
    op.drop_table("artifact_coverage")
    op.drop_table("evidence_events")
    op.drop_table("devices")
    op.drop_table("cases")
