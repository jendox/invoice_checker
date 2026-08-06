"""Bank-specific column mapping presets for statement parsing."""

from dataclasses import dataclass, field

LEGACY_BANK_KEYS: dict[str, str] = {
    "amex_gbp": "amex",
    "amex_usd": "amex",
    "hsbc_gbp": "hsbc",
    "hsbc_usd": "hsbc",
}

STATEMENT_CURRENCIES: tuple[str, ...] = ("GBP", "USD", "EUR")


@dataclass
class BankPreset:
    name: str
    date_columns: list[str] = field(default_factory=list)
    posting_date_columns: list[str] = field(default_factory=list)
    description_columns: list[str] = field(default_factory=list)
    amount_columns: list[str] = field(default_factory=list)
    debit_columns: list[str] = field(default_factory=list)
    credit_columns: list[str] = field(default_factory=list)
    currency_columns: list[str] = field(default_factory=list)
    merchant_columns: list[str] = field(default_factory=list)
    type_columns: list[str] = field(default_factory=list)
    default_currency: str = "GBP"
    skip_columns: list[str] = field(default_factory=lambda: ["invoice", "comment"])


COMMON_DATE = [
    "date",
    "transaction date",
    "posted date",
    "booking date",
    "clearance date",
    "date completed (utc)",
    "date started (utc)",
    "value date",
    "completed date",
]
COMMON_DESCRIPTION = [
    "description",
    "details",
    "narrative",
    "transaction details",
    "memo",
    "appears on your statement as",
    "name",
    "item title",
]
COMMON_AMOUNT = ["amount", "value", "transaction amount", "total amount", "net", "gross"]
COMMON_DEBIT = ["paid out", "money out (gbp)", "debit"]
COMMON_CREDIT = ["paid in", "money in (gbp)", "credit"]
COMMON_CURRENCY = ["currency", "ccy", "payment currency", "orig currency"]


PRESETS: dict[str, BankPreset] = {
    "amex": BankPreset(
        name="amex",
        date_columns=["date"],
        description_columns=["description", "appears on your statement as"],
        amount_columns=["amount"],
        default_currency="GBP",
    ),
    "hsbc": BankPreset(
        name="hsbc",
        date_columns=["date"],
        posting_date_columns=["value date"],
        description_columns=["description"],
        amount_columns=["amount"],
        debit_columns=["paid out"],
        credit_columns=["paid in"],
        default_currency="GBP",
    ),
    "hsbc_csv": BankPreset(
        name="hsbc_csv",
        date_columns=["date"],
        description_columns=["description"],
        amount_columns=["amount"],
        default_currency="GBP",
    ),
    "revolut": BankPreset(
        name="revolut",
        date_columns=["date completed (utc)", "date started (utc)"],
        description_columns=["description"],
        amount_columns=["orig amount", "amount", "total amount"],
        currency_columns=["orig currency", "payment currency"],
        merchant_columns=["beneficiary name", "sender name"],
        default_currency="GBP",
    ),
    "paypal": BankPreset(
        name="paypal",
        date_columns=["date"],
        description_columns=["name", "item title", "subject"],
        amount_columns=["net", "gross"],
        currency_columns=["currency"],
        merchant_columns=["name"],
        type_columns=["type"],
        default_currency="GBP",
    ),
    "barclays": BankPreset(
        name="barclays",
        date_columns=["date"],
        description_columns=["memo", "subcategory"],
        amount_columns=["amount"],
        default_currency="GBP",
    ),
    "capital_on_tap": BankPreset(
        name="capital_on_tap",
        date_columns=["clearance date", "authorisation date"],
        description_columns=["description"],
        amount_columns=["amount"],
        merchant_columns=["merchant name"],
        default_currency="GBP",
    ),
    "generic": BankPreset(
        name="generic",
        date_columns=COMMON_DATE,
        description_columns=COMMON_DESCRIPTION,
        amount_columns=COMMON_AMOUNT,
        debit_columns=COMMON_DEBIT,
        credit_columns=COMMON_CREDIT,
        currency_columns=COMMON_CURRENCY,
        default_currency="GBP",
    ),
}


def normalize_bank_key(bank_key: str) -> str:
    normalized = bank_key.strip().lower()
    return LEGACY_BANK_KEYS.get(normalized, normalized)


def detect_bank_from_filename(filename: str) -> str:
    name = filename.lower()
    rules: list[tuple[str, bool]] = [
        ("revolut_savings", "revolut" in name and "saving" in name),
        ("revolut", "revolut" in name),
        ("amex", "amex" in name),
        ("paypal", "paypal" in name),
        ("barclays", "barclays" in name),
        ("capital_on_tap", "capitalontap" in name or "capital_on_tap" in name),
        ("hsbc_csv", "hsbc" in name and "loan" in name),
        ("hsbc", "hsbc" in name),
    ]
    for bank_key, matched in rules:
        if matched:
            return bank_key
    return "generic"


def detect_currency_from_filename(filename: str) -> str:
    lowered = filename.lower()
    if "$" in filename or "usd" in lowered:
        return "USD"
    if "€" in filename or "eur" in lowered:
        return "EUR"
    return "GBP"


def get_preset(bank_key: str) -> BankPreset:
    return PRESETS.get(normalize_bank_key(bank_key), PRESETS["generic"])
