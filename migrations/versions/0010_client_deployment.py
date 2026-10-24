"""Pin a dedicated database to a single configured licensee."""
from alembic import op
import sqlalchemy as sa
from app.core.config import settings
revision="0010_client_deployment"
down_revision="0009_interest_requests"
branch_labels=None
depends_on=None
def upgrade():
    table=op.create_table('client_deployment',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('client_id',sa.String(80),nullable=False),sa.Column('licensee_id',sa.String(120),nullable=False),sa.Column('license_id',sa.String(120),nullable=False),sa.Column('parent_license_id',sa.String(120)))
    op.bulk_insert(table,[{'id':1,'client_id':settings.client_id,'licensee_id':settings.licensee_id,'license_id':settings.license_id,'parent_license_id':settings.parent_license_id}])
def downgrade():op.drop_table('client_deployment')
