from decimal import Decimal

import pytest

from app.models.enums import TransactionCategory, TransactionStatus
from app.services.classifier.classifier import TransactionClassifier


@pytest.mark.asyncio
async def test_amazon_classification(session):
    classifier = TransactionClassifier()
    _, _, result = await classifier.classify_transaction(
        session,
        "AMZ*MARKETING SVCS AMS.AMAZON.CO",
        "amex",
        "debit",
        Decimal("2250.89"),
    )
    assert result.category == TransactionCategory.AMAZON_TRANSACTION.value
    assert result.requires_invoice is False
    assert result.confidence >= Decimal("0.85")


@pytest.mark.asyncio
async def test_unknown_classification(session):
    classifier = TransactionClassifier()
    _, _, result = await classifier.classify_transaction(
        session,
        "OBSCURE VENDOR XYZ123 UNIQUE",
        "hsbc",
        "debit",
        Decimal("100.00"),
    )
    assert result.category == TransactionCategory.UNKNOWN.value
    assert result.requires_invoice is None
    assert result.status == TransactionStatus.NEEDS_REVIEW.value
    assert result.confidence == Decimal("0.2")


@pytest.mark.asyncio
async def test_google_software_subscription(session):
    classifier = TransactionClassifier()
    _, _, result = await classifier.classify_transaction(
        session,
        "GOOGLE*ADS7924609133 DUBLIN",
        "amex",
        "debit",
        Decimal("500.00"),
    )
    assert result.category == TransactionCategory.SOFTWARE_SUBSCRIPTION.value
    assert result.requires_invoice is True
