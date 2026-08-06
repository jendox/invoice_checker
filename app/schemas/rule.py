from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RuleCreate(BaseModel):
    name: str
    pattern: str
    pattern_type: str = "contains"
    bank_name: str | None = None
    direction: str | None = None
    category: str
    requires_invoice: bool | None = None
    invoice_provider: str | None = None
    invoice_owner: str | None = None
    priority: int = 100
    confidence: Decimal = Decimal("0.8")
    is_active: bool = True


class RuleUpdate(BaseModel):
    name: str | None = None
    pattern: str | None = None
    pattern_type: str | None = None
    bank_name: str | None = None
    direction: str | None = None
    category: str | None = None
    requires_invoice: bool | None = None
    invoice_provider: str | None = None
    invoice_owner: str | None = None
    priority: int | None = None
    confidence: Decimal | None = None
    is_active: bool | None = None


class RuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    pattern: str
    pattern_type: str
    bank_name: str | None
    direction: str | None
    category: str
    requires_invoice: bool | None
    invoice_provider: str | None
    invoice_owner: str | None
    priority: int
    confidence: Decimal
    is_active: bool
    created_at: datetime
