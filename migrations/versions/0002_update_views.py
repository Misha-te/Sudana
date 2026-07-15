"""Add private, unique Update viewer tracking.

Revision ID: 0002_update_views
Revises: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_update_views"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("update_views"):
        op.create_table(
            "update_views",
            sa.Column("id", sa.String(length=32), nullable=False),
            sa.Column("update_id", sa.String(length=32), nullable=False),
            sa.Column("viewer_id", sa.String(length=32), nullable=False),
            sa.Column("first_viewed_at", sa.DateTime(), nullable=False),
            sa.Column("last_viewed_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["update_id"], ["updates.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["viewer_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("update_id", "viewer_id", name="uq_update_viewer"),
        )
        op.create_index("ix_update_views_update_id", "update_views", ["update_id"])
        op.create_index("ix_update_views_viewer_id", "update_views", ["viewer_id"])
        op.create_index(
            "ix_update_views_update_first_viewed",
            "update_views",
            ["update_id", "first_viewed_at"],
        )


def downgrade():
    # Deliberately non-destructive. Viewer history must not be removed by an
    # accidental production downgrade.
    pass
