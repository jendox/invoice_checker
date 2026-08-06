"""Category badge color presets (background, text)."""

DEFAULT_BADGE_BG = "#334155"
DEFAULT_BADGE_TEXT = "#e2e8f0"

CATEGORY_BADGE_COLORS: dict[str, tuple[str, str]] = {
    "amazon_transaction": ("#422006", "#fbbf24"),
    "bank_fee": ("#1e293b", "#94a3b8"),
    "internal_transfer": ("#172554", "#93c5fd"),
    "software_subscription": ("#312e81", "#a5b4fc"),
    "logistics": ("#14532d", "#86efac"),
    "supplier_purchase": ("#581c87", "#d8b4fe"),
    "salary": ("#713f12", "#fcd34d"),
    "revenue": ("#064e3b", "#6ee7b7"),
    "unknown": ("#450a0a", "#fca5a5"),
}


def badge_colors_for_slug(slug: str) -> tuple[str, str]:
    return CATEGORY_BADGE_COLORS.get(slug, (DEFAULT_BADGE_BG, DEFAULT_BADGE_TEXT))
