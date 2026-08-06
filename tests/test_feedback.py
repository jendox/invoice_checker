from datetime import date
from decimal import Decimal

import pytest

from app.models.enums import ClassificationSource, TransactionStatus
from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.schemas.transaction import ClassificationUpdate
from app.services.transaction_service import TransactionService


@pytest.mark.asyncio
async def test_manual_feedback_update(session):
    stmt = StatementFile(
        bank_name="amex",
        company_name="cubetag",
        statement_month="2026-06",
        original_filename="test.xlsx",
    )
    session.add(stmt)
    await session.flush()

    tx = Transaction(
        statement_file_id=stmt.id,
        bank_name="amex",
        transaction_date=date(2026, 6, 1),
        description_raw="MYSTERY VENDOR",
        description_normalized="mystery vendor",
        amount=Decimal("50.00"),
        currency="GBP",
        direction="debit",
        category="unknown",
        requires_invoice=None,
        confidence=Decimal("0.2"),
        classification_source="unknown",
        status=TransactionStatus.NEEDS_REVIEW.value,
        fingerprint="abc123" + "0" * 58,
    )
    session.add(tx)
    await session.commit()

    service = TransactionService()
    updated = await service.update_classification(
        session,
        tx.id,
        ClassificationUpdate(
            category="supplier_purchase",
            requires_invoice=True,
            invoice_provider="Mystery Vendor Ltd",
            status="confirmed",
            comment="Manual review",
        ),
    )

    assert updated.category == "supplier_purchase"
    assert updated.requires_invoice is True
    assert updated.classification_source == ClassificationSource.MANUAL.value
    assert updated.confidence == Decimal("1.0")

    from sqlalchemy import select

    from app.models.feedback import Feedback

    fb = (await session.execute(select(Feedback).where(Feedback.transaction_id == tx.id))).scalar_one()
    assert fb.old_category == "unknown"
    assert fb.new_category == "supplier_purchase"
    assert fb.comment == "Manual review"
