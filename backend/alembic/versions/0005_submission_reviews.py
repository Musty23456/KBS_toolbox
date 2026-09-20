"""Add submission review workflow.

Revision ID: 0005_submission_reviews
Revises: 0004_group_instance_index
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_submission_reviews"
down_revision = "0004_group_instance_index"
branch_labels = None
depends_on = None

review_status_enum = sa.Enum(
    "RECEIVED", "UNDER_REVIEW", "HAS_ISSUES", "APPROVED", "REJECTED", "RESUBMIT",
    name="reviewstatus",
)

def upgrade() -> None:
    review_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column("submissions", sa.Column("review_status", review_status_enum, nullable=False, server_default="RECEIVED"))
    op.create_table(
        "submission_reviews",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submission_id", sa.String(length=36), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", review_status_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_index("ix_submission_reviews_submission_id", "submission_reviews", ["submission_id"])


def downgrade() -> None:
    op.drop_index("ix_submission_reviews_submission_id", table_name="submission_reviews")
    op.drop_column("submissions", "review_status")
    op.drop_table("submission_reviews")
    review_status_enum.drop(op.get_bind(), checkfirst=True)
