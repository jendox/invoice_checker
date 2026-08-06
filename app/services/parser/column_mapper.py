import re
from typing import Any

import pandas as pd

from app.services.parser.bank_presets import (
    COMMON_AMOUNT,
    COMMON_CREDIT,
    COMMON_DATE,
    COMMON_DEBIT,
    COMMON_DESCRIPTION,
    BankPreset,
)


def _normalize_col(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


def find_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized = {_normalize_col(c): c for c in columns}
    for candidate in candidates:
        key = _normalize_col(candidate)
        if key in normalized:
            return normalized[key]
    # Partial match
    for candidate in candidates:
        key = _normalize_col(candidate)
        for ncol, orig in normalized.items():
            if key in ncol or ncol in key:
                return orig
    return None


class ColumnMapper:
    def __init__(self, preset: BankPreset, columns: list[str]) -> None:
        self.preset = preset
        self.columns = columns
        self.date_col = find_column(columns, preset.date_columns or COMMON_DATE)
        self.posting_date_col = find_column(columns, preset.posting_date_columns)
        self.description_col = find_column(columns, preset.description_columns or COMMON_DESCRIPTION)
        self.amount_col = find_column(columns, preset.amount_columns or COMMON_AMOUNT)
        self.debit_col = find_column(columns, preset.debit_columns or COMMON_DEBIT)
        self.credit_col = find_column(columns, preset.credit_columns or COMMON_CREDIT)
        self.currency_col = find_column(columns, preset.currency_columns)
        self.merchant_col = find_column(columns, preset.merchant_columns)
        self.type_col = find_column(columns, preset.type_columns)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.date_col:
            errors.append("Missing date column")
        if not self.description_col:
            errors.append("Missing description column")
        has_amount = self.amount_col is not None
        has_debit_credit = self.debit_col is not None or self.credit_col is not None
        if not has_amount and not has_debit_credit:
            errors.append("Missing amount or debit/credit columns")
        return errors

    def map_row(self, row: pd.Series) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.date_col:
            data["date"] = row.get(self.date_col)
        if self.posting_date_col:
            data["posting_date"] = row.get(self.posting_date_col)
        if self.description_col:
            data["description"] = row.get(self.description_col)
        if self.currency_col:
            data["currency"] = row.get(self.currency_col)
        if self.merchant_col:
            data["merchant"] = row.get(self.merchant_col)
        if self.type_col:
            data["type"] = row.get(self.type_col)

        if self.amount_col:
            data["amount"] = row.get(self.amount_col)
        else:
            debit = row.get(self.debit_col) if self.debit_col else None
            credit = row.get(self.credit_col) if self.credit_col else None
            data["debit"] = debit
            data["credit"] = credit
        return data
