from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    ClassificationSource,
    TransactionCategory,
    TransactionStatus,
)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("fingerprint", name="uq_transaction_fingerprint"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    statement_file_id: Mapped[int] = mapped_column(ForeignKey("statement_files.id"), index=True)
    bank_name: Mapped[str] = mapped_column(String(100), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    posting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description_raw: Mapped[str] = mapped_column(Text)
    description_normalized: Mapped[str] = mapped_column(Text, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    direction: Mapped[str] = mapped_column(String(10))
    account_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default=TransactionCategory.UNKNOWN.value, index=True)
    requires_invoice: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    invoice_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_owner: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("0.0"))
    classification_source: Mapped[str] = mapped_column(
        String(20), default=ClassificationSource.UNKNOWN.value,
    )
    status: Mapped[str] = mapped_column(String(20), default=TransactionStatus.NEW.value, index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    statement_file: Mapped["StatementFile"] = relationship(back_populates="transactions")
    feedback_entries: Mapped[list["Feedback"]] = relationship(back_populates="transaction")


from app.models.feedback import Feedback  # noqa: E402, F401
from app.models.statement_file import StatementFile  # noqa: E402, F401
