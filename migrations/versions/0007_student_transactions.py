"""Deduplicate student banking requests."""
from alembic import op
import sqlalchemy as sa
revision="0007_student_transactions"
down_revision="0006_auth_sessions"
branch_labels=None
depends_on=None
def upgrade():
    op.add_column("ledger_entries",sa.Column("client_request_id",sa.String(36),nullable=True))
    op.create_index("uq_ledger_client_request","ledger_entries",["client_request_id"],unique=True)
def downgrade():
    op.drop_index("uq_ledger_client_request",table_name="ledger_entries")
    op.drop_column("ledger_entries","client_request_id")
