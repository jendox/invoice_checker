from datetime import date
from decimal import Decimal

import pytest

from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionFilters
from app.services.transaction_service import TransactionService
from app.utils.query import parse_optional_date


def test_parse_optional_date_empty_string():
    assert parse_optional_date("") is None
    assert parse_optional_date("   ") is None
    assert parse_optional_date(None) is None
    assert parse_optional_date("2026-06-01") == date(2026, 6, 1)


@pytest.mark.asyncio
async def test_list_transactions_date_range(session):
    stmt = StatementFile(
        bank_name="amex",
        company_name="cubetag",
        statement_month="2026-06",
        original_filename="test.xlsx",
    )
    session.add(stmt)
    await session.flush()

    session.add_all([
        Transaction(
            statement_file_id=stmt.id,
            bank_name="amex",
            transaction_date=date(2026, 5, 31),
            description_raw="May tx",
            description_normalized="may tx",
            amount=Decimal("10.00"),
            currency="GBP",
            direction="debit",
            category="unknown",
            confidence=Decimal("0.2"),
            classification_source="unknown",
            status="needs_review",
            fingerprint="a" * 64,
        ),
        Transaction(
            statement_file_id=stmt.id,
            bank_name="amex",
            transaction_date=date(2026, 6, 15),
            description_raw="June tx",
            description_normalized="june tx",
            amount=Decimal("20.00"),
            currency="GBP",
            direction="debit",
            category="unknown",
            confidence=Decimal("0.2"),
            classification_source="unknown",
            status="needs_review",
            fingerprint="b" * 64,
        ),
    ])
    await session.commit()

    service = TransactionService()
    items, total = await service.list_transactions(
        session,
        TransactionFilters(date_from=date(2026, 6, 1), date_to=date(2026, 6, 30), page_size=50),
    )

    assert total == 1
    assert items[0].description_raw == "June tx"


@pytest.mark.asyncio
async def test_transactions_page_ignores_empty_date_params(client):
    response = await client.get("/transactions?bank_name=amex&date_from=&date_to=")
    assert response.status_code == 200
    assert "Transactions" in response.text
