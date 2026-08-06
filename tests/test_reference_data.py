from datetime import date
from decimal import Decimal

import pytest

from app.models.enums import ClassificationSource, TransactionStatus
from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate
from app.schemas.invoice_owner import InvoiceOwnerCreate
from app.schemas.transaction import ClassificationUpdate
from app.services.category_service import CategoryService
from app.services.classifier.memory_matcher import MemoryMatcher
from app.services.invoice_owner_service import InvoiceOwnerService
from app.services.transaction_service import TransactionService


@pytest.mark.asyncio
async def test_create_category_with_custom_colors(session):
    service = CategoryService()
    created = await service.create(
        session,
        CategoryCreate(
            slug="marketing",
            label="Marketing",
            badge_bg="#1e3a8a",
            badge_text="#bfdbfe",
        ),
    )
    assert created.badge_bg == "#1e3a8a"
    assert created.badge_text == "#bfdbfe"


@pytest.mark.asyncio
async def test_create_invoice_owner(session):
    service = InvoiceOwnerService()
    created = await service.create(session, InvoiceOwnerCreate(name="Boris"))
    assert created.name == "Boris"


@pytest.mark.asyncio
async def test_memory_resolves_unique_invoice_owner(session):
    stmt = StatementFile(
        bank_name="amex",
        company_name="cubetag",
        statement_month="2026-06",
        original_filename="test.xlsx",
    )
    session.add(stmt)
    await session.flush()

    training = Transaction(
        statement_file_id=stmt.id,
        bank_name="amex",
        transaction_date=date(2026, 6, 5),
        description_raw="OPENAI *CHATGPT SUBSCR",
        description_normalized="openai chatgpt subscr",
        amount=Decimal("20.00"),
        currency="GBP",
        direction="debit",
        category="software_subscription",
        requires_invoice=True,
        invoice_provider="OpenAI",
        invoice_owner="Boris",
        confidence=Decimal("1.0"),
        classification_source=ClassificationSource.MANUAL.value,
        status=TransactionStatus.CONFIRMED.value,
        fingerprint="memtest1" + "0" * 58,
    )
    session.add(training)
    await session.commit()

    matcher = MemoryMatcher()
    result = await matcher.find_match(
        session,
        "openai chatgpt subscr",
        "amex",
        Decimal("20.00"),
    )
    assert result is not None
    assert result.invoice_owner == "Boris"


@pytest.mark.asyncio
async def test_memory_leaves_owner_null_when_ambiguous(session):
    stmt = StatementFile(
        bank_name="amex",
        company_name="cubetag",
        statement_month="2026-06",
        original_filename="test.xlsx",
    )
    session.add(stmt)
    await session.flush()

    for idx, owner in enumerate(["Boris", "Anna"], start=1):
        session.add(
            Transaction(
                statement_file_id=stmt.id,
                bank_name="amex",
                transaction_date=date(2026, 6, idx * 5),
                description_raw="OPENAI *CHATGPT SUBSCR",
                description_normalized="openai chatgpt subscr",
                amount=Decimal("20.00"),
                currency="GBP",
                direction="debit",
                category="software_subscription",
                requires_invoice=True,
                invoice_owner=owner,
                confidence=Decimal("1.0"),
                classification_source=ClassificationSource.MANUAL.value,
                status=TransactionStatus.CONFIRMED.value,
                fingerprint=f"ambig{idx}" + "0" * 58,
            ),
        )
    await session.commit()

    matcher = MemoryMatcher()
    result = await matcher.find_match(
        session,
        "openai chatgpt subscr",
        "amex",
        Decimal("20.00"),
    )
    assert result is not None
    assert result.invoice_owner is None


@pytest.mark.asyncio
async def test_manual_feedback_stores_invoice_owner(session):
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
        description_raw="OPENAI *CHATGPT",
        description_normalized="openai chatgpt",
        amount=Decimal("20.00"),
        currency="GBP",
        direction="debit",
        category="unknown",
        confidence=Decimal("0.2"),
        classification_source="unknown",
        status=TransactionStatus.NEEDS_REVIEW.value,
        fingerprint="ownerfb" + "0" * 59,
    )
    session.add(tx)
    await session.commit()

    service = TransactionService()
    updated = await service.update_classification(
        session,
        tx.id,
        ClassificationUpdate(
            category="software_subscription",
            requires_invoice=True,
            invoice_owner="Boris",
            status="confirmed",
        ),
    )
    assert updated.invoice_owner == "Boris"
