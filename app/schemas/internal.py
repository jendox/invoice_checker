from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class ParsedTransaction:
    transaction_date: date
    posting_date: date | None
    description_raw: str
    amount: Decimal
    currency: str
    direction: str
    merchant_name: str | None = None
    account_last4: str | None = None


@dataclass
class ClassificationResult:
    category: str
    requires_invoice: bool | None
    invoice_provider: str | None
    invoice_owner: str | None
    confidence: Decimal
    classification_source: str
    status: str
