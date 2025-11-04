"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("username", sa.String(length=64)),
        sa.Column("first_name", sa.String(length=128)),
        sa.Column("last_name", sa.String(length=128)),
        sa.Column("language_code", sa.String(length=16)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False, unique=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("support_contact", sa.String(length=120)),
        sa.Column("domain_hint", sa.String(length=120)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_products_type"), "products", ["type"], unique=False)

    op.create_table(
        "file_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("path", sa.String(length=255), nullable=False, unique=True),
        sa.Column("os_type", sa.String(length=50)),
        sa.Column("checksum", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_file_assets_product_type"), "file_assets", ["product_type"], unique=False)

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="RUB"),
        sa.Column("digiseller_product_id", sa.String(length=64)),
        sa.Column("payment_url", sa.String(length=512)),
        sa.Column("sort_order", sa.Integer(), server_default="0"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "purchase_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("digiseller_order_id", sa.String(length=120)),
        sa.Column("invoice_url", sa.String(length=512)),
        sa.Column("token", sa.String(length=128), unique=True),
        sa.Column("domain_type", sa.String(length=50)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_purchase_sessions_token_unique",
        "purchase_sessions",
        ["token"],
        unique=True,
        postgresql_where=sa.text("token IS NOT NULL"),
    )

    op.create_table(
        "token_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_id", sa.Integer(), sa.ForeignKey("purchase_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("token_events")
    op.drop_index("ix_purchase_sessions_token_unique", table_name="purchase_sessions")
    op.drop_table("purchase_sessions")
    op.drop_table("product_variants")
    op.drop_index("ix_file_assets_product_type", table_name="file_assets")
    op.drop_table("file_assets")
    op.drop_index("ix_products_type", table_name="products")
    op.drop_table("products")
    op.drop_table("users")
