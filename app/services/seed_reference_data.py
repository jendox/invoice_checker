from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank import Bank
from app.models.category import Category
from app.models.company import Company
from app.utils.category_colors import badge_colors_for_slug

_CATEGORY_DEFS = [
    ("amazon_transaction", "Amazon transaction", 10, False),
    ("bank_fee", "Bank fee", 20, False),
    ("internal_transfer", "Internal transfer", 30, False),
    ("supplier_purchase", "Supplier purchase", 40, True),
    ("software_subscription", "Software subscription", 50, True),
    ("logistics", "Logistics", 60, True),
    ("salary", "Salary", 70, False),
    ("revenue", "Revenue", 80, False),
    ("unknown", "Unknown", 999, None),
]

DEFAULT_CATEGORIES = [
    {
        "slug": slug,
        "label": label,
        "sort_order": sort_order,
        "requires_invoice_default": requires_invoice_default,
        "badge_bg": badge_colors_for_slug(slug)[0],
        "badge_text": badge_colors_for_slug(slug)[1],
    }
    for slug, label, sort_order, requires_invoice_default in _CATEGORY_DEFS
]

DEFAULT_BANKS = [
    {"key": "amex", "display_name": "Amex", "default_currency": "GBP"},
    {"key": "hsbc", "display_name": "HSBC", "default_currency": "GBP"},
    {"key": "hsbc_csv", "display_name": "HSBC CSV/Loan", "default_currency": "GBP"},
    {"key": "revolut", "display_name": "Revolut", "default_currency": "GBP"},
    {"key": "revolut_savings", "display_name": "Revolut Savings", "default_currency": "GBP"},
    {"key": "paypal", "display_name": "PayPal", "default_currency": "GBP"},
    {"key": "barclays", "display_name": "Barclays", "default_currency": "GBP"},
    {"key": "capital_on_tap", "display_name": "Capital on Tap", "default_currency": "GBP"},
    {"key": "generic", "display_name": "Generic fallback", "default_currency": "GBP"},
]

DEFAULT_COMPANIES = [
    {"key": "cubetag", "display_name": "Cubetag"},
    {"key": "hipcrate", "display_name": "Hipcrate"},
    {"key": "doorz", "display_name": "Doorz"},
]


async def seed_reference_data(session: AsyncSession) -> None:
    existing = await session.execute(select(Category.id).limit(1))
    if existing.scalar_one_or_none() is None:
        for row in DEFAULT_CATEGORIES:
            session.add(Category(is_active=True, **row))

    existing = await session.execute(select(Bank.id).limit(1))
    if existing.scalar_one_or_none() is None:
        for row in DEFAULT_BANKS:
            session.add(Bank(is_active=True, **row))

    existing = await session.execute(select(Company.id).limit(1))
    if existing.scalar_one_or_none() is None:
        for row in DEFAULT_COMPANIES:
            session.add(Company(is_active=True, **row))

    await session.commit()
