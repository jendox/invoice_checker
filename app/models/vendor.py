from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    normalized_name: Mapped[str] = mapped_column(String(255), index=True)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    default_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_requires_invoice: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    default_invoice_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_invoice_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
