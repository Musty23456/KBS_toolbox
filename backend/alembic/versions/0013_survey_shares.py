"""survey shares: owner shares a personal survey with other enumerators

Revision ID: 0013_survey_shares
Revises: 0012_survey_scope
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_survey_shares"
down_revision = "0012_survey_scope"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "survey_shares",
        sa.Column("survey_id", sa.String(length=36), sa.ForeignKey("surveys.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade():
    op.drop_table("survey_shares")
