"""switch to yoomoney payments"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_yoomoney"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("purchase_sessions", "digiseller_order_id", new_column_name="payment_id")
    op.add_column(
        "purchase_sessions",
        sa.Column("payment_provider", sa.String(length=64), nullable=False, server_default="yoomoney"),
    )
    op.alter_column("purchase_sessions", "payment_provider", server_default=None)


def downgrade() -> None:
    op.alter_column("purchase_sessions", "payment_id", new_column_name="digiseller_order_id")
    op.drop_column("purchase_sessions", "payment_provider")
