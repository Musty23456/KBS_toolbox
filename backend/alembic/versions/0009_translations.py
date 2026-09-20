"""add survey translations

Revision ID: 0009_translations
Revises: 0008_location_intelligence
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_translations"
down_revision = "0008_location_intelligence"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "translations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("survey_id", sa.String(length=36), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("field", sa.String(length=50), nullable=False),
        sa.Column("language_code", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.UniqueConstraint("survey_id", "entity_type", "entity_id", "field", "language_code", name="uq_translation_target"),
    )
    op.create_index("ix_translations_survey_id", "translations", ["survey_id"])
    op.create_index("ix_translations_entity_id", "translations", ["entity_id"])
    op.create_index("ix_translations_language_code", "translations", ["language_code"])


def downgrade():
    op.drop_index("ix_translations_language_code", table_name="translations")
    op.drop_index("ix_translations_entity_id", table_name="translations")
    op.drop_index("ix_translations_survey_id", table_name="translations")
    op.drop_table("translations")
