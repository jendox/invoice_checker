from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification_rule import ClassificationRule
from app.models.enums import ClassificationSource, TransactionCategory, TransactionStatus
from app.schemas.internal import ClassificationResult
from app.services.classifier.llm_classifier import LLMClassifier, MockLLMClassifier
from app.services.classifier.memory_matcher import MemoryMatcher
from app.services.classifier.normalizer import extract_merchant_name, normalize_description
from app.services.classifier.rule_engine import RuleEngine, RuleMatchContext
from app.services.classifier.vendor_matcher import VendorMatcher


class TransactionClassifier:
    def __init__(
        self,
        llm: LLMClassifier | None = None,
        memory: MemoryMatcher | None = None,
        vendor: VendorMatcher | None = None,
    ) -> None:
        self._llm = llm or MockLLMClassifier()
        self._memory = memory or MemoryMatcher()
        self._vendor = vendor or VendorMatcher()

    async def classify_transaction(
        self,
        session: AsyncSession,
        description_raw: str,
        bank_name: str,
        direction: str,
        amount: Decimal,
        account_last4: str | None = None,
        *,
        skip_memory: bool = False,
    ) -> tuple[str, str | None, ClassificationResult]:
        description_normalized = normalize_description(description_raw)
        merchant_name = extract_merchant_name(description_raw)

        # 1. Memory
        if not skip_memory:
            memory_result = await self._memory.find_match(
                session,
                description_normalized,
                bank_name,
                amount,
                account_last4=account_last4,
            )
            if memory_result:
                return description_normalized, merchant_name, memory_result

        # 2. Rules
        rules_result = await session.execute(
            select(ClassificationRule).where(ClassificationRule.is_active.is_(True)),
        )
        rules = list(rules_result.scalars().all())
        rule_engine = RuleEngine(rules)
        ctx = RuleMatchContext(
            description_normalized=description_normalized,
            description_raw=description_raw,
            bank_name=bank_name,
            direction=direction,
            merchant_name=merchant_name,
        )
        rule_result = rule_engine.match(ctx)
        if rule_result:
            return description_normalized, merchant_name, rule_result

        # 3. Vendor
        vendor_result = await self._vendor.find_match(session, description_normalized, merchant_name)
        if vendor_result:
            return description_normalized, merchant_name, vendor_result

        # 4. LLM (mock)
        llm_result = await self._llm.classify(
            description_raw, description_normalized, str(amount), bank_name,
        )
        if llm_result:
            return description_normalized, merchant_name, llm_result

        # 5. Unknown
        return description_normalized, merchant_name, ClassificationResult(
            category=TransactionCategory.UNKNOWN.value,
            requires_invoice=None,
            invoice_provider=None,
            invoice_owner=None,
            confidence=Decimal("0.2"),
            classification_source=ClassificationSource.UNKNOWN.value,
            status=TransactionStatus.NEEDS_REVIEW.value,
        )
