"""Add submission media records.

Revision ID: 0006_submission_media
Revises: 0005_submission_reviews
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_submission_media"
down_revision = "0005_submission_reviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "submission_media",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submission_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("group_instance_index", sa.Integer(), nullable=True),
        sa.Column("kind", sa.Enum("PHOTO", "AUDIO", "SIGNATURE", name="mediakind"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_submission_media_submission_id", "submission_media", ["submission_id"])
    op.create_index("ix_submission_media_question_id", "submission_media", ["question_id"])


def downgrade() -> None:
    op.drop_index("ix_submission_media_question_id", table_name="submission_media")
    op.drop_index("ix_submission_media_submission_id", table_name="submission_media")
    op.drop_table("submission_media")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="mediakind").drop(bind, checkfirst=True)
