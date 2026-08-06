from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassificationSource, TransactionCategory, TransactionStatus
from app.models.vendor import Vendor
from app.schemas.internal import ClassificationResult


class VendorMatcher:
    async def find_match(
        self,
        session: AsyncSession,
        description_normalized: str,
        merchant_name: str | None,
    ) -> ClassificationResult | None:
        result = await session.execute(select(Vendor))
        vendors = result.scalars().all()

        search_text = description_normalized
        if merchant_name:
            search_text = f"{search_text} {merchant_name.lower()}"

        for vendor in vendors:
            names = [vendor.normalized_name] + [a.lower() for a in (vendor.aliases or [])]
            if not any(name and name in search_text for name in names):
                continue
            return ClassificationResult(
                category=vendor.default_category or TransactionCategory.UNKNOWN.value,
                requires_invoice=vendor.default_requires_invoice,
                invoice_provider=vendor.default_invoice_provider or vendor.name,
                invoice_owner=vendor.default_invoice_owner,
                confidence=Decimal("0.75"),
                classification_source=ClassificationSource.VENDOR.value,
                status=TransactionStatus.NEW.value
                if vendor.default_category != TransactionCategory.UNKNOWN.value
                else TransactionStatus.NEEDS_REVIEW.value,
            )
        return None
