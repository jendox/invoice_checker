from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ClassificationRule(Base):
    __tablename__ = "classification_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    pattern: Mapped[str] = mapped_column(String(500))
    pattern_type: Mapped[str] = mapped_column(String(20))
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    category: Mapped[str] = mapped_column(String(50))
    requires_invoice: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    invoice_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.8"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
