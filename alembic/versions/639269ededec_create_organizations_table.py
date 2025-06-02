"""create_organizations_table

Revision ID: 793c73812407
Revises: add_user_sessions
Create Date: 2025-06-02 11:51:44.368499

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision: str = "793c73812407"
down_revision: Union[str, None] = "add_user_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create organizations table only."""
    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column(
            "name", sa.String(length=255), nullable=False, comment="Organization name"
        ),
        sa.Column(
            "domain",
            sa.String(length=255),
            nullable=True,
            comment="Primary email domain for the organization",
        ),
        sa.Column(
            "billing_email",
            sa.String(length=255),
            nullable=True,
            comment="Billing contact email address",
        ),
        sa.Column(
            "billing_address",
            sa.NVARCHAR(),
            nullable=True,
            comment="Billing address details",
        ),
        sa.Column(
            "stripe_customer_id",
            sa.String(length=255),
            nullable=True,
            comment="Stripe customer identifier for billing",
        ),
        sa.Column(
            "metadata",
            sa.NVARCHAR(),
            nullable=True,
            comment="Additional organization information (JSON data)",
        ),
        sa.Column("id", mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column(
            "index_id",
            sa.BigInteger(),
            sa.Identity(always=False, start=1, increment=1),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, comment="Soft delete flag"
        ),
        sa.Column(
            "tenant_id",
            mssql.UNIQUEIDENTIFIER(),
            nullable=False,
            comment="Multi-tenant isolation key",
        ),
        sa.CheckConstraint(
            "domain IS NULL OR domain LIKE '%.%'", name="ck_organizations_domain_format"
        ),
        sa.PrimaryKeyConstraint(
            "id", mssql_clustered=False
        ),  # Non-clustered primary key
        sa.UniqueConstraint("index_id"),
    )

    # Create indexes
    op.create_index(
        "ix_organizations_index_id",
        "organizations",
        ["index_id"],
        unique=True,
        mssql_clustered=True,
    )
    op.create_index(
        op.f("ix_organizations_is_deleted"),
        "organizations",
        ["is_deleted"],
        unique=False,
    )
    op.create_index(
        "ix_organizations_stripe_customer_id",
        "organizations",
        ["stripe_customer_id"],
        unique=False,
        mssql_where="stripe_customer_id IS NOT NULL",
    )
    op.create_index(
        "ix_organizations_tenant_active",
        "organizations",
        ["tenant_id", "is_deleted", "index_id"],
        unique=False,
        mssql_where=sa.text("is_deleted = 0"),
    )
    op.create_index(
        "ix_organizations_tenant_domain",
        "organizations",
        ["tenant_id", "domain"],
        unique=False,
        mssql_where="domain IS NOT NULL AND is_deleted = 0",
    )
    op.create_index(
        op.f("ix_organizations_tenant_id"), "organizations", ["tenant_id"], unique=False
    )
    op.create_index(
        "ix_organizations_tenant_id_lookup",
        "organizations",
        ["tenant_id", "id"],
        unique=False,
        mssql_where=sa.text("is_deleted = 0"),
    )
    op.create_index(
        "ix_organizations_tenant_name",
        "organizations",
        ["tenant_id", "name"],
        unique=True,
        mssql_where="is_deleted = 0",
    )

    # Add foreign key constraint to tenants table
    op.create_foreign_key(
        "fk_organizations_tenant_id", "organizations", "tenants", ["tenant_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema - Remove organizations table."""
    # Drop foreign key constraint
    op.drop_constraint(
        "fk_organizations_tenant_id", "organizations", type_="foreignkey"
    )

    # Drop indexes
    op.drop_index(
        "ix_organizations_tenant_name",
        table_name="organizations",
        mssql_where="is_deleted = 0",
    )
    op.drop_index(
        "ix_organizations_tenant_id_lookup",
        table_name="organizations",
        mssql_where=sa.text("is_deleted = 0"),
    )
    op.drop_index(op.f("ix_organizations_tenant_id"), table_name="organizations")
    op.drop_index(
        "ix_organizations_tenant_domain",
        table_name="organizations",
        mssql_where="domain IS NOT NULL AND is_deleted = 0",
    )
    op.drop_index(
        "ix_organizations_tenant_active",
        table_name="organizations",
        mssql_where=sa.text("is_deleted = 0"),
    )
    op.drop_index(
        "ix_organizations_stripe_customer_id",
        table_name="organizations",
        mssql_where="stripe_customer_id IS NOT NULL",
    )
    op.drop_index(op.f("ix_organizations_is_deleted"), table_name="organizations")
    op.drop_index(
        "ix_organizations_index_id", table_name="organizations", mssql_clustered=True
    )

    # Drop table
    op.drop_table("organizations")
