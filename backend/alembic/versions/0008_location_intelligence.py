"""Add location intelligence indexes."""
from alembic import op

revision = "0008_location_intelligence"
down_revision = "0007_devices"
branch_labels = None
depends_on = None

def upgrade():
    op.create_index("ix_submissions_gps_latitude", "submissions", ["gps_latitude"])
    op.create_index("ix_submissions_gps_longitude", "submissions", ["gps_longitude"])
    op.create_index("ix_locations_level_parent", "locations", ["level", "parent_id"])

def downgrade():
    op.drop_index("ix_locations_level_parent", table_name="locations")
    op.drop_index("ix_submissions_gps_longitude", table_name="submissions")
    op.drop_index("ix_submissions_gps_latitude", table_name="submissions")
