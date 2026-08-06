from decimal import Decimal

from app.models.classification_rule import ClassificationRule
from app.models.enums import PatternType
from app.services.classifier.rule_engine import RuleEngine, RuleMatchContext


def _ctx(description: str, bank: str = "amex") -> RuleMatchContext:
    return RuleMatchContext(
        description_normalized=description.lower(),
        description_raw=description,
        bank_name=bank,
        direction="debit",
        merchant_name="Test Merchant",
    )


def test_amazon_rule_matches():
    rules = [
        ClassificationRule(
            id=1,
            name="Amazon",
            pattern="amazon",
            pattern_type=PatternType.CONTAINS.value,
            category="amazon_transaction",
            requires_invoice=False,
            priority=200,
            confidence=Decimal("0.9"),
            is_active=True,
        ),
    ]
    engine = RuleEngine(rules)
    result = engine.match(_ctx("AMZ*MARKETING SVCS AMS.AMAZON.CO"))
    assert result is not None
    assert result.category == "amazon_transaction"
    assert result.requires_invoice is False


def test_exact_rule_priority():
    rules = [
        ClassificationRule(
            id=1,
            name="Contains transfer",
            pattern="transfer",
            pattern_type=PatternType.CONTAINS.value,
            category="internal_transfer",
            requires_invoice=False,
            priority=100,
            confidence=Decimal("0.8"),
            is_active=True,
        ),
        ClassificationRule(
            id=2,
            name="Exact match",
            pattern="internal transfer",
            pattern_type=PatternType.EXACT.value,
            category="internal_transfer",
            requires_invoice=False,
            priority=50,
            confidence=Decimal("0.95"),
            is_active=True,
        ),
    ]
    engine = RuleEngine(rules)
    result = engine.match(_ctx("internal transfer"))
    assert result is not None
    assert result.confidence == Decimal("0.95")


def test_bank_filter():
    rules = [
        ClassificationRule(
            id=1,
            name="HSBC only",
            pattern="fee",
            pattern_type=PatternType.CONTAINS.value,
            bank_name="hsbc",
            category="bank_fee",
            requires_invoice=False,
            priority=100,
            confidence=Decimal("0.85"),
            is_active=True,
        ),
    ]
    engine = RuleEngine(rules)
    assert engine.match(_ctx("monthly fee", bank="hsbc")) is not None
    assert engine.match(_ctx("monthly fee", bank="amex")) is None
