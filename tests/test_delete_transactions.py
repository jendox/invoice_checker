from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.enums import ClassificationSource, TransactionStatus
from app.models.feedback import Feedback
from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.schemas.transaction import DeleteTransactionsRequest
from app.services.transaction_service import TransactionService


@pytest.mark.asyncio
async def test_delete_transactions_by_category(session):
    stmt = StatementFile(
        bank_name="amex",
        company_name="cubetag",
        statement_month="2026-06",
        original_filename="test.xlsx",
    )
    session.add(stmt)
    await session.flush()

    keep = Transaction(
        statement_file_id=stmt.id,
        bank_name="amex",
        transaction_date=date(2026, 6, 1),
        description_raw="KEEP ME",
        description_normalized="keep me",
        amount=Decimal("10.00"),
        currency="GBP",
        direction="debit",
        category="revenue",
        confidence=Decimal("0.8"),
        classification_source=ClassificationSource.RULE.value,
        status=TransactionStatus.NEW.value,
        fingerprint="keep1" + "0" * 59,
    )
    remove = Transaction(
        statement_file_id=stmt.id,
        bank_name="amex",
        transaction_date=date(2026, 6, 2),
        description_raw="DELETE ME",
        description_normalized="delete me",
        amount=Decimal("20.00"),
        currency="GBP",
        direction="debit",
        category="unknown",
        confidence=Decimal("0.2"),
        classification_source=ClassificationSource.UNKNOWN.value,
        status=TransactionStatus.NEEDS_REVIEW.value,
        fingerprint="del1" + "0" * 60,
    )
    session.add_all([keep, remove])
    await session.commit()

    service = TransactionService()
    deleted = await service.delete_transactions(
        session,
        DeleteTransactionsRequest(category="unknown"),
    )

    assert deleted == 1
    remaining = (await session.execute(select(Transaction))).scalars().all()
    assert len(remaining) == 1
    assert remaining[0].description_raw == "KEEP ME"
    feedback = (await session.execute(select(Feedback))).scalars().all()
    assert feedback == []


@pytest.mark.asyncio
async def test_delete_transactions_returns_zero_when_no_matches(session):
    service = TransactionService()
    deleted = await service.delete_transactions(
        session,
        DeleteTransactionsRequest(bank_name="missing"),
    )
    assert deleted == 0
