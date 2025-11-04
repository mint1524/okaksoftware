"""introduce yoomoney wallet payments"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_yoomoney_wallet"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("product_variants") as batch_op:
        batch_op.alter_column("digiseller_product_id", new_column_name="external_id")

    with op.batch_alter_table("purchase_sessions") as batch_op:
        batch_op.alter_column("digiseller_order_id", new_column_name="payment_label")
        batch_op.add_column(sa.Column("payment_provider", sa.String(length=64), nullable=False, server_default="yoomoney_wallet"))
        batch_op.add_column(sa.Column("payment_amount", sa.Numeric(10, 2), nullable=True))
        batch_op.add_column(sa.Column("payment_currency", sa.String(length=8), nullable=True))
        batch_op.create_index("ix_purchase_sessions_payment_label", ["payment_label"], unique=True)
    op.execute("UPDATE purchase_sessions SET payment_provider = 'yoomoney_wallet'")
    with op.batch_alter_table("purchase_sessions") as batch_op:
        batch_op.alter_column("payment_provider", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("product_variants") as batch_op:
        batch_op.alter_column("external_id", new_column_name="digiseller_product_id")

    with op.batch_alter_table("purchase_sessions") as batch_op:
        batch_op.drop_index("ix_purchase_sessions_payment_label")
        batch_op.alter_column("payment_label", new_column_name="digiseller_order_id")
        batch_op.drop_column("payment_provider")
        batch_op.drop_column("payment_amount")
        batch_op.drop_column("payment_currency")
