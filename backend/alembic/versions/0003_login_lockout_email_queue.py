"""Sign-in lockout counters on users and delivery tracking on the email outbox.

Revision ID: 0003_lockout_email_queue
Revises: 0002_legal_contact
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_lockout_email_queue"
down_revision: Union[str, Sequence[str], None] = "0002_legal_contact"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("failed_login_count", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("locked_until", sa.DateTime(), nullable=True))
    with op.batch_alter_table("email_messages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("attempts", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("last_attempt_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("sent_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_email_messages_status", ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("email_messages", schema=None) as batch_op:
        batch_op.drop_index("ix_email_messages_status")
        batch_op.drop_column("sent_at")
        batch_op.drop_column("last_attempt_at")
        batch_op.drop_column("attempts")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("locked_until")
        batch_op.drop_column("failed_login_count")
