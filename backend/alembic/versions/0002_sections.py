"""survey sections/pages
Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "survey_sections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("survey_version_id", sa.String(36), sa.ForeignKey("survey_versions.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("questions", sa.Column("section_id", sa.String(36), sa.ForeignKey("survey_sections.id"), nullable=True))

def downgrade():
    op.drop_column("questions", "section_id")
    op.drop_table("survey_sections")
