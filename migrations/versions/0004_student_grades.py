"""Persist classroom assignment grades."""
from alembic import op
import sqlalchemy as sa
revision = "0004_student_grades"
down_revision = "0003_transfer_pairs"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("grades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("graded_by", sa.Integer(), nullable=False),
        sa.Column("points_earned", sa.Numeric(10, 2), nullable=False),
        sa.Column("points_possible", sa.Numeric(10, 2), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("assignment_id", "student_id", name="uq_grade_assignment_student"),
        sa.CheckConstraint("points_possible > 0 AND points_earned >= 0 AND points_earned <= points_possible", name="ck_grade_points"))
    op.create_index("ix_grades_assignment_id", "grades", ["assignment_id"])
    op.create_index("ix_grades_student_id", "grades", ["student_id"])

def downgrade():
    op.drop_table("grades")
