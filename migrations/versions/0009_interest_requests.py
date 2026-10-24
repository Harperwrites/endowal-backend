"""Capture nonbinding investor, donor and school interest."""
from alembic import op
import sqlalchemy as sa
revision="0009_interest_requests"
down_revision="0008_demo_credit"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table('interest_requests',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('name',sa.String(120),nullable=False),sa.Column('email',sa.String(255),nullable=False),sa.Column('audience',sa.String(20),nullable=False),sa.Column('organization',sa.String(180)),sa.Column('note',sa.Text()),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
def downgrade():op.drop_table('interest_requests')
