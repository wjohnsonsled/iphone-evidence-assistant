"""add candidate evidence integrity infrastructure

Revision ID: 0002_evidence_integrity
Revises: 0001_initial_schema
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_evidence_integrity"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def _scope_columns():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "integrity_evidence_objects", *_scope_columns(),
        sa.Column("evidence_source_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_uuid", sa.Uuid(), nullable=False, unique=True),
        sa.Column("parent_evidence_uuid", sa.Uuid()),
        sa.Column("evidence_kind", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_locator", sa.Text(), nullable=False),
        sa.Column("logical_identifier", sa.String(255), nullable=False),
        sa.Column("intake_method", sa.String(128), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registered_by_actor_id", sa.Uuid(), nullable=False),
        sa.Column("integrity_state", sa.String(64), nullable=False),
        sa.Column("lifecycle_state", sa.String(64), nullable=False),
        sa.Column("lock_state", sa.String(64), nullable=False),
        sa.Column("provenance_node_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_table(
        "integrity_hash_observations", *_scope_columns(),
        sa.Column("evidence_uuid", sa.Uuid(), nullable=False),
        sa.Column("algorithm", sa.String(32), nullable=False),
        sa.Column("digest", sa.String(128)),
        sa.Column("byte_length", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("component", sa.String(128), nullable=False),
        sa.Column("component_version", sa.String(64), nullable=False),
        sa.Column("role", sa.String(64), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_code", sa.String(128)),
    )
    op.create_table(
        "integrity_audit_events", *_scope_columns(),
        sa.Column("evidence_uuid", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("failure_code", sa.String(128)),
        sa.UniqueConstraint("tenant_id", "sequence", name="uq_integrity_audit_tenant_sequence"),
    )
    op.create_table(
        "integrity_custody_events", *_scope_columns(),
        sa.Column("evidence_uuid", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("prior_event_id", sa.Uuid()),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("actor_type", sa.String(64), nullable=False),
        sa.Column("action_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("component", sa.String(128), nullable=False),
        sa.Column("component_version", sa.String(64), nullable=False),
        sa.Column("environment_id", sa.String(128), nullable=False),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column("result", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.Uuid(), nullable=False),
        sa.Column("failure_code", sa.String(128)),
        sa.Column("failure_detail", sa.Text()),
        sa.UniqueConstraint("evidence_uuid", "sequence", name="uq_integrity_custody_evidence_sequence"),
    )
    op.create_table(
        "integrity_provenance_nodes", *_scope_columns(),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("stable_locator", sa.Text(), nullable=False),
    )
    op.create_table(
        "integrity_provenance_edges", *_scope_columns(),
        sa.Column("source_node_id", sa.Uuid(), nullable=False),
        sa.Column("target_node_id", sa.Uuid(), nullable=False),
        sa.Column("relationship", sa.String(64), nullable=False),
        sa.Column("parser_id", sa.String(128)),
        sa.Column("parser_version", sa.String(64)),
    )


def downgrade() -> None:
    for table in (
        "integrity_provenance_edges", "integrity_provenance_nodes",
        "integrity_custody_events", "integrity_audit_events",
        "integrity_hash_observations", "integrity_evidence_objects",
    ):
        op.drop_table(table)
