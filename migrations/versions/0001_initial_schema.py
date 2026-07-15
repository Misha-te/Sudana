"""Create the initial Sudana PostgreSQL schema."""
from alembic import op
from models import Base

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind())

def downgrade():
    # Intentionally non-destructive: production user data must never be
    # removed by an accidental migration downgrade.
    pass
