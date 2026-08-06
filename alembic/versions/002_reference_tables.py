"""Reference tables and invoice_owner support.

Revision ID: 002
Revises: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_CATEGORIES = [
    {"slug": "amazon_transaction", "label": "Amazon transaction", "sort_order": 10, "requires_invoice_default": False},
    {"slug": "bank_fee", "label": "Bank fee", "sort_order": 20, "requires_invoice_default": False},
    {"slug": "internal_transfer", "label": "Internal transfer", "sort_order": 30, "requires_invoice_default": False},
    {"slug": "supplier_purchase", "label": "Supplier purchase", "sort_order": 40, "requires_invoice_default": True},
    {"slug": "software_subscription", "label": "Software subscription", "sort_order": 50, "requires_invoice_default": True},
    {"slug": "logistics", "label": "Logistics", "sort_order": 60, "requires_invoice_default": True},
    {"slug": "salary", "label": "Salary", "sort_order": 70, "requires_invoice_default": False},
    {"slug": "revenue", "label": "Revenue", "sort_order": 80, "requires_invoice_default": False},
    {"slug": "unknown", "label": "Unknown", "sort_order": 999, "requires_invoice_default": None},
]

DEFAULT_BANKS = [
    {"key": "amex_gbp", "display_name": "Amex GBP", "default_currency": "GBP"},
    {"key": "amex_usd", "display_name": "Amex USD", "default_currency": "USD"},
    {"key": "hsbc_gbp", "display_name": "HSBC", "default_currency": "GBP"},
    {"key": "hsbc_usd", "display_name": "HSBC USD", "default_currency": "USD"},
    {"key": "hsbc_csv", "display_name": "HSBC CSV/Loan", "default_currency": "GBP"},
    {"key": "revolut", "display_name": "Revolut", "default_currency": "GBP"},
    {"key": "revolut_savings", "display_name": "Revolut Savings", "default_currency": "GBP"},
    {"key": "paypal", "display_name": "PayPal", "default_currency": "GBP"},
    {"key": "barclays", "display_name": "Barclays", "default_currency": "GBP"},
    {"key": "capital_on_tap", "display_name": "Capital on Tap", "default_currency": "GBP"},
    {"key": "generic", "display_name": "Generic fallback", "default_currency": "GBP"},
]

DEFAULT_COMPANIES = [
    {"key": "cubetag", "display_name": "Cubetag"},
    {"key": "hipcrate", "display_name": "Hipcrate"},
    {"key": "doorz", "display_name": "Doorz"},
]


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("requires_invoice_default", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"])

    op.create_table(
        "banks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("default_currency", sa.String(length=3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_banks_key", "banks", ["key"])

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key"),
    )
    op.create_index("ix_companies_key", "companies", ["key"])

    op.create_table(
        "invoice_owners",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.add_column("transactions", sa.Column("invoice_owner", sa.String(length=100), nullable=True))
    op.create_index("ix_transactions_invoice_owner", "transactions", ["invoice_owner"])

    op.add_column("feedback", sa.Column("old_invoice_owner", sa.String(length=100), nullable=True))
    op.add_column("feedback", sa.Column("new_invoice_owner", sa.String(length=100), nullable=True))

    op.add_column("classification_rules", sa.Column("invoice_owner", sa.String(length=100), nullable=True))
    op.add_column("vendors", sa.Column("default_invoice_owner", sa.String(length=100), nullable=True))

    categories = sa.table(
        "categories",
        sa.column("slug", sa.String),
        sa.column("label", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("requires_invoice_default", sa.Boolean),
    )
    op.bulk_insert(
        categories,
        [{**row, "is_active": True} for row in DEFAULT_CATEGORIES],
    )

    banks = sa.table(
        "banks",
        sa.column("key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("default_currency", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        banks,
        [{**row, "is_active": True} for row in DEFAULT_BANKS],
    )

    companies = sa.table(
        "companies",
        sa.column("key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        companies,
        [{**row, "is_active": True} for row in DEFAULT_COMPANIES],
    )


def downgrade() -> None:
    op.drop_column("vendors", "default_invoice_owner")
    op.drop_column("classification_rules", "invoice_owner")
    op.drop_column("feedback", "new_invoice_owner")
    op.drop_column("feedback", "old_invoice_owner")
    op.drop_index("ix_transactions_invoice_owner", table_name="transactions")
    op.drop_column("transactions", "invoice_owner")
    op.drop_table("invoice_owners")
    op.drop_table("companies")
    op.drop_index("ix_banks_key", table_name="banks")
    op.drop_table("banks")
    op.drop_index("ix_categories_slug", table_name="categories")
    op.drop_table("categories")
