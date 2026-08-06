from pathlib import Path

import pytest

from app.models.classification_rule import ClassificationRule
from app.models.enums import PatternType
from app.services.classifier.rule_engine import RuleEngine, RuleMatchContext
from app.services.classifier.normalizer import normalize_description
from app.services.parser.statement_parser import StatementParser

STATEMENTS_DIR = Path(__file__).resolve().parent.parent / "statements"
PAYPAL_FILE = STATEMENTS_DIR / "hipcrate" / "+PayPal 1-30.06.26.xlsx"


@pytest.fixture
def paypal_transactions():
    if not PAYPAL_FILE.exists():
        pytest.skip(f"File not found: {PAYPAL_FILE}")
    content = PAYPAL_FILE.read_bytes()
    return StatementParser().parse_file(content, PAYPAL_FILE.name, "paypal")


def test_paypal_includes_type_in_description(paypal_transactions):
    assert len(paypal_transactions) == 34
    express = [tx for tx in paypal_transactions if "Express Checkout Payment" in tx.description_raw]
    assert len(express) == 20
    assert express[0].description_raw.startswith("Express Checkout Payment | ")


def test_paypal_currency_conversion_without_name(paypal_transactions):
    fx = [tx for tx in paypal_transactions if tx.description_raw == "General Currency Conversion"]
    assert len(fx) == 2


def test_paypal_general_payment_has_merchant(paypal_transactions):
    payout = [tx for tx in paypal_transactions if "General Payment" in tx.description_raw]
    assert len(payout) == 1
    assert payout[0].merchant_name == "Serge Radschenko"
    assert payout[0].description_raw == "General Payment | Serge Radschenko"


def test_paypal_rules_classify_revenue_and_payout():
    rules = [
        ClassificationRule(
            id=1,
            name="PayPal revenue checkout",
            pattern="express checkout payment",
            pattern_type=PatternType.CONTAINS.value,
            bank_name=None,
            direction=None,
            category="revenue",
            requires_invoice=False,
            invoice_provider=None,
            invoice_owner=None,
            priority=100,
            confidence=0.8,
            is_active=True,
        ),
        ClassificationRule(
            id=2,
            name="PayPal contractor payout",
            pattern="general payment",
            pattern_type=PatternType.CONTAINS.value,
            bank_name=None,
            direction=None,
            category="supplier_purchase",
            requires_invoice=True,
            invoice_provider="merchant_name",
            invoice_owner=None,
            priority=100,
            confidence=0.8,
            is_active=True,
        ),
    ]
    engine = RuleEngine(rules)

    revenue_ctx = RuleMatchContext(
        description_normalized=normalize_description(
            "Express Checkout Payment | Judith Silver",
        ),
        description_raw="Express Checkout Payment | Judith Silver",
        bank_name="paypal",
        direction="credit",
        merchant_name="Judith Silver",
    )
    revenue = engine.match(revenue_ctx)
    assert revenue is not None
    assert revenue.category == "revenue"
    assert revenue.requires_invoice is False

    payout_ctx = RuleMatchContext(
        description_normalized=normalize_description(
            "General Payment | Serge Radschenko",
        ),
        description_raw="General Payment | Serge Radschenko",
        bank_name="paypal",
        direction="debit",
        merchant_name="Serge Radschenko",
    )
    payout = engine.match(payout_ctx)
    assert payout is not None
    assert payout.category == "supplier_purchase"
    assert payout.requires_invoice is True
    assert payout.invoice_provider == "Serge Radschenko"
