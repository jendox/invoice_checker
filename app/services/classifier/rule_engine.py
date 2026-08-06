from dataclasses import dataclass
from decimal import Decimal

from app.models.classification_rule import ClassificationRule
from app.models.enums import PatternType
from app.schemas.internal import ClassificationResult


@dataclass
class RuleMatchContext:
    description_normalized: str
    description_raw: str
    bank_name: str
    direction: str
    merchant_name: str | None


class RuleEngine:
    def __init__(self, rules: list[ClassificationRule]) -> None:
        self._rules = sorted(
            [r for r in rules if r.is_active],
            key=lambda r: (
                {"exact": 0, "regex": 1, "contains": 2}.get(r.pattern_type, 3),
                -r.priority,
            ),
        )

    def match(self, ctx: RuleMatchContext) -> ClassificationResult | None:
        for rule in self._rules:
            if rule.bank_name and rule.bank_name.lower() != ctx.bank_name.lower():
                continue
            if rule.direction and rule.direction.lower() != ctx.direction.lower():
                continue
            if not self._pattern_matches(rule, ctx):
                continue

            provider = rule.invoice_provider
            if provider == "merchant_name":
                provider = ctx.merchant_name

            status = "needs_review" if rule.category == "unknown" else "new"
            return ClassificationResult(
                category=rule.category,
                requires_invoice=rule.requires_invoice,
                invoice_provider=provider,
                invoice_owner=rule.invoice_owner,
                confidence=Decimal(str(rule.confidence)),
                classification_source="rule",
                status=status,
            )
        return None

    @staticmethod
    def _pattern_matches(rule: ClassificationRule, ctx: RuleMatchContext) -> bool:
        text = ctx.description_normalized
        raw = ctx.description_raw.lower()

        if rule.pattern_type == PatternType.EXACT.value:
            return text == rule.pattern.lower() or raw == rule.pattern.lower()
        if rule.pattern_type == PatternType.REGEX.value:
            import re

            return bool(re.search(rule.pattern, text, re.I) or re.search(rule.pattern, raw, re.I))
        # contains
        needle = rule.pattern.lower()
        return needle in text or needle in raw
