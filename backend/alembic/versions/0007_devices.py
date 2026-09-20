"""Add device management and sync telemetry."""
from alembic import op
import sqlalchemy as sa
revision = "0007_devices"
down_revision = "0006_submission_media"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("devices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("app_version", sa.String(length=50), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=False, server_default="ANDROID"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(length=30), nullable=True),
        sa.Column("failed_sync_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sync_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_devices_device_id", "devices", ["device_id"], unique=True)
    op.create_index("ix_devices_user_id", "devices", ["user_id"])

def downgrade():
    op.drop_index("ix_devices_user_id", table_name="devices")
    op.drop_index("ix_devices_device_id", table_name="devices")
    op.drop_table("devices")
