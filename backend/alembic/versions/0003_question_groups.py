"""question groups and repeatable group metadata

Revision ID: 0003_question_groups
Revises: 0002_sections
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_question_groups"
down_revision = "0002_sections"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "question_groups",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("survey_version_id", sa.String(length=36), sa.ForeignKey("survey_versions.id"), nullable=False),
        sa.Column("section_id", sa.String(length=36), sa.ForeignKey("survey_sections.id"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repeatable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("min_repeats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_repeats", sa.Integer(), nullable=True),
    )
    op.add_column("questions", sa.Column("group_id", sa.String(length=36), nullable=True))
    op.create_foreign_key("fk_questions_group_id", "questions", "question_groups", ["group_id"], ["id"])

def downgrade():
    op.drop_constraint("fk_questions_group_id", "questions", type_="foreignkey")
    op.drop_column("questions", "group_id")
    op.drop_table("question_groups")
