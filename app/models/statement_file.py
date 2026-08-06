from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StatementFile(Base):
    __tablename__ = "statement_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_name: Mapped[str] = mapped_column(String(100), index=True)
    company_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    statement_month: Mapped[str] = mapped_column(String(7), index=True)  # YYYY-MM
    currency: Mapped[str] = mapped_column(String(3), default="GBP")
    original_filename: Mapped[str] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="statement_file")


from app.models.transaction import Transaction  # noqa: E402, F401
