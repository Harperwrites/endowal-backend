"""Preserve standalone opening balances as ledger entries.
Revision ID: 0002_ledger_balances
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
revision = "0002_ledger_balances"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

def upgrade():
    op.execute(sa.text("""
        INSERT INTO ledger_entries (wallet_id, amount, entry_type, source, memo)
        SELECT w.id, abs(w.balance),
               CASE WHEN w.balance > 0 THEN 'deposit' ELSE 'withdrawal' END,
               'teacher_grant', 'Opening balance carried forward'
        FROM student_wallets w
        WHERE w.balance != 0 AND NOT EXISTS
            (SELECT 1 FROM ledger_entries e WHERE e.wallet_id = w.id)
    """))

def downgrade():
    # Opening entries are financial history and must not be discarded.
    pass
