from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY_BANK_KEYS = {
    "amex_gbp": "amex",
    "amex_usd": "amex",
    "hsbc_gbp": "hsbc",
    "hsbc_usd": "hsbc",
}


def upgrade() -> None:
    op.add_column(
        "statement_files",
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="GBP"),
    )

    for legacy_key, bank_key in LEGACY_BANK_KEYS.items():
        op.execute(
            sa.text("UPDATE transactions SET bank_name = :bank_key WHERE bank_name = :legacy_key").bindparams(
                bank_key=bank_key,
                legacy_key=legacy_key,
            ),
        )
        op.execute(
            sa.text(
                "UPDATE statement_files SET bank_name = :bank_key WHERE bank_name = :legacy_key",
            ).bindparams(
                bank_key=bank_key,
                legacy_key=legacy_key,
            ),
        )

    op.execute(
        sa.text(
            "UPDATE banks SET key = 'amex', display_name = 'Amex' "
            "WHERE key = 'amex_gbp' AND NOT EXISTS (SELECT 1 FROM banks AS b WHERE b.key = 'amex')",
        ),
    )
    op.execute(
        sa.text(
            "UPDATE banks SET key = 'hsbc', display_name = 'HSBC' "
            "WHERE key = 'hsbc_gbp' AND NOT EXISTS (SELECT 1 FROM banks AS b WHERE b.key = 'hsbc')",
        ),
    )
    op.execute(sa.text("DELETE FROM banks WHERE key IN ('amex_usd', 'amex_gbp', 'hsbc_usd', 'hsbc_gbp')"))
    op.execute(sa.text("UPDATE banks SET display_name = 'Amex' WHERE key = 'amex'"))
    op.execute(sa.text("UPDATE banks SET display_name = 'HSBC' WHERE key = 'hsbc'"))


def downgrade() -> None:
    op.drop_column("statement_files", "currency")
