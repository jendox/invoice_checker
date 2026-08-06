from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginatedResponse


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    statement_file_id: int
    bank_name: str
    transaction_date: date
    posting_date: date | None
    description_raw: str
    description_normalized: str
    amount: Decimal
    currency: str
    direction: str
    account_last4: str | None
    merchant_name: str | None
    category: str
    requires_invoice: bool | None
    invoice_provider: str | None
    invoice_owner: str | None
    confidence: Decimal
    classification_source: str
    status: str
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(PaginatedResponse):
    items: list[TransactionRead]


class ClassificationUpdate(BaseModel):
    category: str | None = None
    requires_invoice: bool | None = None
    invoice_provider: str | None = None
    invoice_owner: str | None = None
    status: str | None = None
    comment: str | None = None


class TransactionFilters(BaseModel):
    bank_name: str | None = None
    statement_month: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    requires_invoice: bool | None = None
    status: str | None = None
    category: str | None = None
    company_name: str | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class TransactionScopeRequest(BaseModel):
    bank_name: str | None = None
    statement_month: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    requires_invoice: bool | None = None
    status: str | None = None
    category: str | None = None
    company_name: str | None = None
    search: str | None = None


class ReclassifyRequest(TransactionScopeRequest):
    skip_memory: bool = True


class ReclassifyResponse(BaseModel):
    updated: int
    skipped: int


class DeleteTransactionsRequest(TransactionScopeRequest):
    pass


class DeleteTransactionsResponse(BaseModel):
    deleted: int
