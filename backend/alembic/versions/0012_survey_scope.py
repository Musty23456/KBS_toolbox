"""add survey scope (GLOBAL / PERSONAL)

Revision ID: 0012_survey_scope
Revises: 0011_password_reset_requests
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_survey_scope"
down_revision = "0011_password_reset_requests"
branch_labels = None
depends_on = None


def upgrade():
    # Every existing survey stays GLOBAL, so nothing changes for current data.
    op.add_column(
        "surveys",
        sa.Column("scope", sa.String(length=20), nullable=False, server_default="GLOBAL"),
    )
    op.create_index("ix_surveys_created_by_id", "surveys", ["created_by_id"])


def downgrade():
    op.drop_index("ix_surveys_created_by_id", table_name="surveys")
    op.drop_column("surveys", "scope")
