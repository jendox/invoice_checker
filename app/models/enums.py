import enum


class TransactionDirection(enum.StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class TransactionCategory(enum.StrEnum):
    AMAZON_TRANSACTION = "amazon_transaction"
    BANK_FEE = "bank_fee"
    INTERNAL_TRANSFER = "internal_transfer"
    SUPPLIER_PURCHASE = "supplier_purchase"
    SOFTWARE_SUBSCRIPTION = "software_subscription"
    LOGISTICS = "logistics"
    SALARY = "salary"
    REVENUE = "revenue"
    UNKNOWN = "unknown"


class ClassificationSource(enum.StrEnum):
    RULE = "rule"
    MEMORY = "memory"
    MANUAL = "manual"
    LLM = "llm"
    VENDOR = "vendor"
    UNKNOWN = "unknown"


class TransactionStatus(enum.StrEnum):
    NEW = "new"
    CONFIRMED = "confirmed"
    NEEDS_REVIEW = "needs_review"
    RESOLVED = "resolved"


class PatternType(enum.StrEnum):
    CONTAINS = "contains"
    REGEX = "regex"
    EXACT = "exact"
