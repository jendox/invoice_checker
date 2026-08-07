import hashlib
import re
from decimal import Decimal

# Patterns to strip from descriptions (transaction IDs, refs)
_ID_PATTERNS = [
    re.compile(r"\bAT\d{10,}\b", re.I),
    re.compile(r"\bRBD\d+[A-Z0-9]+\b", re.I),
    re.compile(r"\b\d{16,}\b"),
    re.compile(r"/TMS/.*?GMT", re.I),
    re.compile(r"/MID/\s*[\d.]+", re.I),
    re.compile(r"Foreign Spend Amount:.*?(?=$)", re.I),
    re.compile(r"Commission Amount:.*?(?=$)", re.I),
    re.compile(r"Currency Exchange Rate:.*?(?=$)", re.I),
    re.compile(r"Visa Exchange Rate", re.I),
    re.compile(r"\*{6}\d{4}"),
]


MAX_MERCHANT_NAME_LENGTH = 80


def normalize_description(raw: str) -> str:
    text = raw.lower().strip()
    for pattern in _ID_PATTERNS:
        text = pattern.sub(" ", text)
    text = re.sub(r"[^\w\s&*.-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_merchant_name(description: str) -> str | None:
    normalized = normalize_description(description)
    if not normalized:
        return None
    # Take first meaningful chunk before common separators
    parts = re.split(r"\s{2,}|\|", description.strip())
    candidate = parts[0].strip()
    if len(candidate) > MAX_MERCHANT_NAME_LENGTH:
        candidate = candidate[:MAX_MERCHANT_NAME_LENGTH]
    return candidate if candidate else None


def make_fingerprint(
    bank_name: str,
    transaction_date,
    amount: Decimal,
    currency: str,
    description_normalized: str,
) -> str:
    normalized_amount = amount.quantize(Decimal("0.01"))
    normalized_currency = currency.strip().upper()[:3]
    raw = (
        f"{bank_name}|{transaction_date}|{normalized_amount}|"
        f"{normalized_currency}|{description_normalized}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()
