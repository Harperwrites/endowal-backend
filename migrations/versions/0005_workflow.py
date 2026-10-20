"""Assignment turn-ins and classroom messaging."""
from alembic import op
import sqlalchemy as sa
revision="0005_workflow"
down_revision="0004_student_grades"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("assignment_submissions",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("assignment_id",sa.Integer(),nullable=False),sa.Column("student_id",sa.Integer(),nullable=False),sa.Column("content",sa.Text(),nullable=False),sa.Column("submitted_at",sa.DateTime(timezone=True),nullable=False),sa.UniqueConstraint("assignment_id","student_id",name="uq_work_submission"))
    for name in ["assignment_id","student_id"]: op.create_index("ix_assignment_submissions_"+name,"assignment_submissions",[name])
    op.create_table("messages",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("classroom_id",sa.Integer(),nullable=False),sa.Column("sender_id",sa.Integer(),nullable=False),sa.Column("recipient_id",sa.Integer(),nullable=False),sa.Column("body",sa.Text(),nullable=False),sa.Column("sent_at",sa.DateTime(timezone=True),nullable=False),sa.Column("read_at",sa.DateTime(timezone=True)))
    for name in ["classroom_id","sender_id","recipient_id"]: op.create_index("ix_messages_"+name,"messages",[name])
def downgrade():
    op.drop_table("messages");op.drop_table("assignment_submissions")
