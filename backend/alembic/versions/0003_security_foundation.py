"""add tenant-scoped security foundation

Revision ID: 0003_security_foundation
Revises: 0002_evidence_integrity
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_security_foundation"
down_revision = "0002_evidence_integrity"
branch_labels = None
depends_on = None


def _identity_columns():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_actor_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "security_tenants",
        *_identity_columns(),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_security_tenants_version_positive"),
        sa.UniqueConstraint("slug", name="uq_security_tenants_slug"),
    )
    op.create_index("ix_security_tenants_slug", "security_tenants", ["slug"])
    op.create_index(
        "ix_security_tenants_created_by_actor_id",
        "security_tenants",
        ["created_by_actor_id"],
    )

    op.create_table(
        "security_principals",
        *_identity_columns(),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("identity_provider", sa.String(128), nullable=False),
        sa.Column("external_subject", sa.String(255), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_security_principals_version_positive"),
        sa.UniqueConstraint(
            "identity_provider",
            "external_subject",
            name="uq_security_principal_external_identity",
        ),
    )
    op.create_index(
        "ix_security_principals_created_by_actor_id",
        "security_principals",
        ["created_by_actor_id"],
    )

    op.create_table(
        "security_tenant_memberships",
        *_identity_columns(),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("role_key", sa.String(128), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_security_memberships_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["security_tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["principal_id"], ["security_principals.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "tenant_id",
            "principal_id",
            "role_key",
            name="uq_security_membership_tenant_principal_role",
        ),
    )
    for column in ("tenant_id", "principal_id", "created_by_actor_id"):
        op.create_index(
            f"ix_security_tenant_memberships_{column}",
            "security_tenant_memberships",
            [column],
        )

    op.create_table(
        "security_cases",
        *_identity_columns(),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.CheckConstraint("version > 0", name="ck_security_cases_version_positive"),
        sa.ForeignKeyConstraint(["tenant_id"], ["security_tenants.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("id", "tenant_id", name="uq_security_cases_id_tenant"),
    )
    op.create_index("ix_security_cases_tenant_id", "security_cases", ["tenant_id"])
    op.create_index(
        "ix_security_cases_created_by_actor_id",
        "security_cases",
        ["created_by_actor_id"],
    )
    op.create_index("ix_security_cases_tenant_name", "security_cases", ["tenant_id", "name"])

    op.create_table(
        "security_evidence_sources",
        *_identity_columns(),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sa.String(128), nullable=False),
        sa.Column("source_locator", sa.Text(), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registered_by_actor_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint(
            "version > 0",
            name="ck_security_evidence_sources_version_positive",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["security_tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["case_id", "tenant_id"],
            ["security_cases.id", "security_cases.tenant_id"],
            name="fk_security_source_case_tenant",
            ondelete="RESTRICT",
        ),
    )
    for column in ("tenant_id", "case_id", "created_by_actor_id", "registered_by_actor_id"):
        op.create_index(
            f"ix_security_evidence_sources_{column}",
            "security_evidence_sources",
            [column],
        )


def downgrade() -> None:
    op.drop_table("security_evidence_sources")
    op.drop_table("security_cases")
    op.drop_table("security_tenant_memberships")
    op.drop_table("security_principals")
    op.drop_table("security_tenants")
