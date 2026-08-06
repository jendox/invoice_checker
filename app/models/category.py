from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.category_colors import DEFAULT_BADGE_BG, DEFAULT_BADGE_TEXT


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(100))
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_invoice_default: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    badge_bg: Mapped[str] = mapped_column(String(7), default=DEFAULT_BADGE_BG)
    badge_text: Mapped[str] = mapped_column(String(7), default=DEFAULT_BADGE_TEXT)
