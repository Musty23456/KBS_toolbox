"""Add repeatable-group instance index to submission answers.

Revision ID: 0004_group_instance_index
Revises: 0003_question_groups
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_group_instance_index"
down_revision = "0003_question_groups"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("submission_answers", sa.Column("group_instance_index", sa.Integer(), nullable=True))
    op.create_index("ix_submission_answers_group_instance", "submission_answers", ["submission_id", "question_id", "group_instance_index"])

def downgrade() -> None:
    op.drop_index("ix_submission_answers_group_instance", table_name="submission_answers")
    op.drop_column("submission_answers", "group_instance_index")
