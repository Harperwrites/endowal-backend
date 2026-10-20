"""Identify both sides of transfers to protect paired activity."""
from alembic import op
import sqlalchemy as sa
revision = "0003_transfer_pairs"
down_revision = "0002_ledger_balances"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("ledger_entries", sa.Column("transfer_id", sa.String(36), nullable=True))
    op.create_index("ix_ledger_entries_transfer_id", "ledger_entries", ["transfer_id"])
def downgrade():
    op.drop_index("ix_ledger_entries_transfer_id", table_name="ledger_entries")
    op.drop_column("ledger_entries", "transfer_id")
