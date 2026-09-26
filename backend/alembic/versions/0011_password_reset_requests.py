"""replace password reset tokens with admin-mediated reset requests

Revision ID: 0011_password_reset_requests
Revises: 0010_password_reset_tokens
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_password_reset_requests"
down_revision = "0010_password_reset_tokens"
branch_labels = None
depends_on = None


password_reset_request_status = sa.Enum(
    "PENDING",
    "RESOLVED",
    name="passwordresetrequeststatus",
)


def upgrade():
    password_reset_request_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "password_reset_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            password_reset_request_status,
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column(
            "resolved_by_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_password_reset_requests_user_id",
        "password_reset_requests",
        ["user_id"],
    )

    op.create_index(
        "ix_password_reset_requests_status",
        "password_reset_requests",
        ["status"],
    )

    op.drop_table("password_reset_tokens")


def downgrade():
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
    )

    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
    )

    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )

    op.create_index(
        "ix_password_reset_tokens_expires_at",
        "password_reset_tokens",
        ["expires_at"],
    )

    op.drop_index(
        "ix_password_reset_requests_status",
        table_name="password_reset_requests",
    )

    op.drop_index(
        "ix_password_reset_requests_user_id",
        table_name="password_reset_requests",
    )

    op.drop_table("password_reset_requests")

    password_reset_request_status.drop(op.get_bind(), checkfirst=True)
