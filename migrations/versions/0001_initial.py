"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.Enum("teacher", "student", "admin", name="user_role"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "classrooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("school_name", sa.String(length=255), nullable=True),
        sa.Column("grade_level", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("classroom_id", sa.Integer(), nullable=False, index=True),
        sa.Column("student_id", sa.Integer(), nullable=False, index=True),
        sa.Column("status", sa.Enum("active", "archived", name="enrollment_status"), nullable=False),
        sa.UniqueConstraint("classroom_id", "student_id", name="uq_enrollment_class_student"),
    )

    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("classroom_id", sa.Integer(), nullable=False, index=True),
        sa.Column("created_by", sa.Integer(), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("target_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.Enum("draft", "active", "closed", name="assignment_status"), nullable=False),
    )

    op.create_table(
        "student_wallets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("classroom_id", sa.Integer(), nullable=False, index=True),
        sa.Column("student_id", sa.Integer(), nullable=False, index=True),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("classroom_id", "student_id", name="uq_wallet_class_student"),
    )

    op.create_table(
        "wallet_buckets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wallet_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("percent_target", sa.Numeric(5, 2), nullable=True),
        sa.UniqueConstraint("wallet_id", "name", name="uq_bucket_wallet_name"),
    )

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("wallet_id", sa.Integer(), nullable=False, index=True),
        sa.Column("assignment_id", sa.Integer(), nullable=True, index=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("entry_type", sa.Enum("deposit", "withdrawal", name="ledger_entry_type"), nullable=False),
        sa.Column("source", sa.Enum("teacher_grant", "student_action", name="ledger_entry_source"), nullable=False),
        sa.Column("memo", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "budget_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), nullable=False, index=True),
        sa.Column("student_id", sa.Integer(), nullable=False, index=True),
        sa.Column("total_planned", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("submitted", "approved", "revise", name="budget_status"), nullable=False),
        sa.UniqueConstraint("assignment_id", "student_id", name="uq_submission_assignment_student"),
    )

    op.create_table(
        "budget_line_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), nullable=False, index=True),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("budget_line_items")
    op.drop_table("budget_submissions")
    op.drop_table("ledger_entries")
    op.drop_table("wallet_buckets")
    op.drop_table("student_wallets")
    op.drop_table("assignments")
    op.drop_table("enrollments")
    op.drop_table("classrooms")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS budget_status")
    op.execute("DROP TYPE IF EXISTS ledger_entry_source")
    op.execute("DROP TYPE IF EXISTS ledger_entry_type")
    op.execute("DROP TYPE IF EXISTS assignment_status")
    op.execute("DROP TYPE IF EXISTS enrollment_status")
    op.execute("DROP TYPE IF EXISTS user_role")
