"""Persist fictional classroom credit profiles and accounts."""
from alembic import op
import sqlalchemy as sa
revision="0008_demo_credit"
down_revision="0007_student_transactions"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("credit_profiles",sa.Column("user_id",sa.Integer(),primary_key=True),sa.Column("score",sa.Integer(),nullable=False),sa.Column("as_of",sa.Date(),nullable=False),sa.Column("inquiries",sa.Integer(),nullable=False),sa.CheckConstraint("score >= 300 AND score <= 850",name="ck_demo_credit_score"),sa.CheckConstraint("inquiries >= 0",name="ck_credit_inquiries"))
    op.create_table("credit_accounts",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),nullable=False),sa.Column("name",sa.String(120),nullable=False),sa.Column("credit_limit",sa.Numeric(12,2),nullable=False),sa.Column("balance",sa.Numeric(12,2),nullable=False),sa.Column("payments_total",sa.Integer(),nullable=False),sa.Column("payments_on_time",sa.Integer(),nullable=False),sa.Column("opened_on",sa.Date(),nullable=False),sa.CheckConstraint("balance >= 0 AND credit_limit > 0 AND balance <= credit_limit",name="ck_credit_account_amounts"),sa.CheckConstraint("payments_total >= 0 AND payments_on_time >= 0 AND payments_on_time <= payments_total",name="ck_credit_payment_counts"))
    op.create_index("ix_credit_accounts_user_id","credit_accounts",["user_id"])
def downgrade():
    op.drop_table("credit_accounts");op.drop_table("credit_profiles")
