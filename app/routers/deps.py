from typing import Annotated

from fastapi import Depends, Query

from app.schemas.transaction import TransactionFilters
from app.utils.query import parse_optional_date


def get_transaction_filters(
    bank_name: str | None = None,
    statement_month: str | None = None,
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    requires_invoice: bool | None = None,
    status: str | None = None,
    category: str | None = None,
    company_name: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> TransactionFilters:
    return TransactionFilters(
        bank_name=bank_name,
        statement_month=statement_month,
        date_from=parse_optional_date(date_from),
        date_to=parse_optional_date(date_to),
        requires_invoice=requires_invoice,
        status=status,
        category=category,
        company_name=company_name,
        search=search,
        page=page,
        page_size=page_size,
    )


TransactionFiltersDep = Annotated[TransactionFilters, Depends(get_transaction_filters)]
