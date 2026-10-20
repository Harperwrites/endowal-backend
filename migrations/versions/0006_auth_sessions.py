"""Remember signed-in devices with revocable sessions."""
from alembic import op
import sqlalchemy as sa
revision="0006_auth_sessions"
down_revision="0005_workflow"
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("auth_sessions",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),nullable=False),sa.Column("token_hash",sa.String(64),nullable=False,unique=True),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_auth_sessions_user_id","auth_sessions",["user_id"])
def downgrade():op.drop_table("auth_sessions")
