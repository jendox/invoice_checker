"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "statement_files",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_name", sa.String(length=100), nullable=False),
        sa.Column("company_name", sa.String(length=100), nullable=True),
        sa.Column("statement_month", sa.String(length=7), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_statement_files_bank_name", "statement_files", ["bank_name"])
    op.create_index("ix_statement_files_company_name", "statement_files", ["company_name"])
    op.create_index("ix_statement_files_statement_month", "statement_files", ["statement_month"])

    op.create_table(
        "classification_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("pattern", sa.String(length=500), nullable=False),
        sa.Column("pattern_type", sa.String(length=20), nullable=False),
        sa.Column("bank_name", sa.String(length=100), nullable=True),
        sa.Column("direction", sa.String(length=10), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("requires_invoice", sa.Boolean(), nullable=True),
        sa.Column("invoice_provider", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("default_category", sa.String(length=50), nullable=True),
        sa.Column("default_requires_invoice", sa.Boolean(), nullable=True),
        sa.Column("default_invoice_provider", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_vendors_normalized_name", "vendors", ["normalized_name"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("statement_file_id", sa.Integer(), nullable=False),
        sa.Column("bank_name", sa.String(length=100), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("posting_date", sa.Date(), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=False),
        sa.Column("description_normalized", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("account_last4", sa.String(length=4), nullable=True),
        sa.Column("merchant_name", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("requires_invoice", sa.Boolean(), nullable=True),
        sa.Column("invoice_provider", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("classification_source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["statement_file_id"], ["statement_files.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fingerprint", name="uq_transaction_fingerprint"),
    )
    op.create_index("ix_transactions_bank_name", "transactions", ["bank_name"])
    op.create_index("ix_transactions_category", "transactions", ["category"])
    op.create_index("ix_transactions_description_normalized", "transactions", ["description_normalized"])
    op.create_index("ix_transactions_fingerprint", "transactions", ["fingerprint"])
    op.create_index("ix_transactions_requires_invoice", "transactions", ["requires_invoice"])
    op.create_index("ix_transactions_statement_file_id", "transactions", ["statement_file_id"])
    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_transaction_date", "transactions", ["transaction_date"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("old_category", sa.String(length=50), nullable=True),
        sa.Column("new_category", sa.String(length=50), nullable=True),
        sa.Column("old_requires_invoice", sa.Boolean(), nullable=True),
        sa.Column("new_requires_invoice", sa.Boolean(), nullable=True),
        sa.Column("old_invoice_provider", sa.String(length=255), nullable=True),
        sa.Column("new_invoice_provider", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedback_transaction_id", "feedback", ["transaction_id"])


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("transactions")
    op.drop_table("vendors")
    op.drop_table("classification_rules")
    op.drop_table("statement_files")
