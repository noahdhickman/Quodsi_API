"""Add user sessions table and session tracking columns

Revision ID: add_user_sessions
Revises: [REPLACE_WITH_YOUR_LATEST_REVISION]
Create Date: 2025-06-02 09:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "add_user_sessions"
down_revision = "8ae6f504f994"  # Replace with your latest migration ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user sessions table and session tracking columns to users table"""

    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column("id", mssql.UNIQUEIDENTIFIER(), nullable=False, primary_key=True),
        sa.Column("user_id", mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column("tenant_id", mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column("session_token", sa.String(255), nullable=True),
        sa.Column("client_type", sa.String(50), nullable=False),
        sa.Column("session_type", sa.String(50), nullable=False, server_default="web"),
        sa.Column("client_info", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign key constraints
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        # Indexes for performance
        sa.Index("ix_user_sessions_user_id", "user_id"),
        sa.Index("ix_user_sessions_tenant_id", "tenant_id"),
        sa.Index("ix_user_sessions_is_active", "is_active"),
        sa.Index("ix_user_sessions_started_at", "started_at"),
        sa.Index(
            "ix_user_sessions_user_tenant_active", "user_id", "tenant_id", "is_active"
        ),
    )

    # Add session tracking columns to users table
    # Note: Check if these columns already exist in your users table
    # and comment out any that already exist

    # Add last_session_start column
    try:
        op.add_column(
            "users", sa.Column("last_session_start", sa.DateTime(), nullable=True)
        )
    except Exception:
        # Column might already exist
        pass

    # Add last_active_at column (if it doesn't exist)
    try:
        op.add_column(
            "users", sa.Column("last_active_at", sa.DateTime(), nullable=True)
        )
    except Exception:
        # Column might already exist
        pass

    # Add total_usage_minutes column (if it doesn't exist)
    try:
        op.add_column(
            "users",
            sa.Column(
                "total_usage_minutes", sa.Integer(), nullable=True, server_default="0"
            ),
        )
    except Exception:
        # Column might already exist
        pass


def downgrade() -> None:
    """Remove user sessions table and session tracking columns"""

    # Drop the user_sessions table
    op.drop_table("user_sessions")

    # Remove session tracking columns from users table
    # Note: Be careful with these - only drop columns that were added in this migration

    try:
        op.drop_column("users", "last_session_start")
    except Exception:
        # Column might not exist or might be needed by other code
        pass

    # Only drop these if they were added in this migration
    # Comment out if they existed before
    try:
        op.drop_column("users", "last_active_at")
    except Exception:
        pass

    try:
        op.drop_column("users", "total_usage_minutes")
    except Exception:
        pass
