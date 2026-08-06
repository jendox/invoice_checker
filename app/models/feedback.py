from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    old_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    old_requires_invoice: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    new_requires_invoice: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    old_invoice_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_invoice_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    old_invoice_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_invoice_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transaction: Mapped["Transaction"] = relationship(back_populates="feedback_entries")


from app.models.transaction import Transaction  # noqa: E402, F401
