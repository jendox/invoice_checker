from datetime import date
from decimal import Decimal

import pytest

from app.models.classification_rule import ClassificationRule
from app.models.enums import ClassificationSource, PatternType, TransactionStatus
from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.schemas.transaction import ReclassifyRequest
from app.services.transaction_service import TransactionService


@pytest.mark.asyncio
async def test_reclassify_applies_new_rule(session):
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
        description_raw="BRAND NEW VENDOR XYZ",
        description_normalized="brand new vendor xyz",
        amount=Decimal("99.00"),
        currency="GBP",
        direction="debit",
        category="unknown",
        requires_invoice=None,
        confidence=Decimal("0.2"),
        classification_source=ClassificationSource.UNKNOWN.value,
        status=TransactionStatus.NEEDS_REVIEW.value,
        fingerprint="reclass1" + "0" * 58,
    )
    session.add(tx)

    session.add(
        ClassificationRule(
            name="Brand vendor",
            pattern="brand new vendor",
            pattern_type=PatternType.CONTAINS.value,
            category="supplier_purchase",
            requires_invoice=True,
            priority=150,
            confidence=Decimal("0.9"),
            is_active=True,
        ),
    )
    await session.commit()

    service = TransactionService()
    updated, skipped = await service.reclassify_transactions(
        session,
        ReclassifyRequest(skip_memory=True),
    )

    assert updated == 1
    assert skipped == 0
    assert tx.category == "supplier_purchase"
    assert tx.requires_invoice is True
    assert tx.classification_source == ClassificationSource.RULE.value


@pytest.mark.asyncio
async def test_reclassify_skips_manual_transactions(session):
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
        transaction_date=date(2026, 6, 2),
        description_raw="MANUAL VENDOR",
        description_normalized="manual vendor",
        amount=Decimal("10.00"),
        currency="GBP",
        direction="debit",
        category="salary",
        requires_invoice=False,
        confidence=Decimal("1.0"),
        classification_source=ClassificationSource.MANUAL.value,
        status=TransactionStatus.CONFIRMED.value,
        fingerprint="reclass2" + "0" * 58,
    )
    session.add(tx)
    await session.commit()

    service = TransactionService()
    updated, skipped = await service.reclassify_transactions(session, ReclassifyRequest())

    assert updated == 0
    assert skipped == 0
    assert tx.category == "salary"
