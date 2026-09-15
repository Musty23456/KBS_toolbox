"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("ADMINISTRATOR", "SUPERVISOR", "ENUMERATOR", name="rolename"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "revoked_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("jti", sa.String(36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_revoked_tokens_jti", "revoked_tokens", ["jti"], unique=True)

    op.create_table(
        "locations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "surveys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "PUBLISHED", "ARCHIVED", name="surveystatus"), nullable=False),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "survey_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("survey_id", sa.String(36), sa.ForeignKey("surveys.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("survey_version_id", sa.String(36), sa.ForeignKey("survey_versions.id"), nullable=False),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column(
            "type",
            sa.Enum(
                "SHORT_TEXT", "LONG_TEXT", "INTEGER", "DECIMAL", "DATE", "TIME", "DATETIME",
                "SINGLE_CHOICE", "MULTIPLE_CHOICE", "DROPDOWN", "YES_NO", "GPS", "PHOTO",
                "AUDIO", "SIGNATURE", "BARCODE", name="questiontype",
            ),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("min_value", sa.Float(), nullable=True),
        sa.Column("max_value", sa.Float(), nullable=True),
        sa.Column("min_length", sa.Integer(), nullable=True),
        sa.Column("max_length", sa.Integer(), nullable=True),
        sa.Column("regex_pattern", sa.String(500), nullable=True),
        sa.Column("relevance_expression", sa.Text(), nullable=True),
        sa.Column("calculation_expression", sa.Text(), nullable=True),
        sa.Column("default_value", sa.String(500), nullable=True),
        sa.Column("cascade_parent_question_id", sa.String(36), sa.ForeignKey("questions.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "choices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("question_id", sa.String(36), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("label", sa.String(500), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cascade_parent_value", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("survey_id", sa.String(36), sa.ForeignKey("surveys.id"), nullable=False),
        sa.Column("survey_version_id", sa.String(36), sa.ForeignKey("survey_versions.id"), nullable=False),
        sa.Column("submitted_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_submission_uuid", sa.String(36), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "UPLOADING", "UPLOADED", "SYNCED", "FAILED", name="submissionstatus"),
            nullable=False,
        ),
        sa.Column("gps_latitude", sa.Float(), nullable=True),
        sa.Column("gps_longitude", sa.Float(), nullable=True),
        sa.Column("collected_at", sa.String(64), nullable=True),
        sa.Column("synced_at", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("client_submission_uuid", name="uq_submission_client_uuid"),
    )

    op.create_table(
        "submission_answers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("submission_id", sa.String(36), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("question_id", sa.String(36), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("media_reference", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "sync_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("submission_id", sa.String(36), sa.ForeignKey("submissions.id"), nullable=False, unique=True),
        sa.Column("client_device_id", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "IN_PROGRESS", "SUCCESS", "FAILED", name="syncstatus"),
            nullable=False,
        ),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("sync_metadata")
    op.drop_table("submission_answers")
    op.drop_table("submissions")
    op.drop_table("choices")
    op.drop_table("questions")
    op.drop_table("survey_versions")
    op.drop_table("surveys")
    op.drop_table("locations")
    op.drop_table("revoked_tokens")
    op.drop_table("users")
    sa.Enum(name="rolename").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="surveystatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="questiontype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="submissionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="syncstatus").drop(op.get_bind(), checkfirst=True)
