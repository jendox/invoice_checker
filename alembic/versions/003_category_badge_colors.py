"""Add category badge colors.

Revision ID: 003
Revises: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.utils.category_colors import CATEGORY_BADGE_COLORS, DEFAULT_BADGE_BG, DEFAULT_BADGE_TEXT

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("badge_bg", sa.String(length=7), nullable=False, server_default=DEFAULT_BADGE_BG),
    )
    op.add_column(
        "categories",
        sa.Column("badge_text", sa.String(length=7), nullable=False, server_default=DEFAULT_BADGE_TEXT),
    )

    categories = sa.table(
        "categories",
        sa.column("slug", sa.String),
        sa.column("badge_bg", sa.String),
        sa.column("badge_text", sa.String),
    )
    for slug, (bg, text) in CATEGORY_BADGE_COLORS.items():
        op.execute(
            categories.update()
            .where(categories.c.slug == slug)
            .values(badge_bg=bg, badge_text=text),
        )


def downgrade() -> None:
    op.drop_column("categories", "badge_text")
    op.drop_column("categories", "badge_bg")
