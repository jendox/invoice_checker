import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

from app.models.enums import TransactionDirection
from app.schemas.internal import ParsedTransaction
from app.services.parser.bank_presets import (
    BankPreset,
    detect_bank_from_filename,
    get_preset,
    normalize_bank_key,
)
from app.services.parser.column_mapper import ColumnMapper, _normalize_col

MIN_HEADER_KEYWORD_SCORE = 2
DATE_FORMATS = (
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d.%m.%Y",
)
INVALID_DECIMAL_TOKENS = {".", "-", "+"}


def _header_keywords(preset: BankPreset) -> set[str]:
    return {
        _normalize_col(keyword)
        for keyword in (
            *preset.date_columns,
            *preset.description_columns,
            *preset.amount_columns,
            *preset.debit_columns,
            *preset.credit_columns,
            "date",
            "description",
            "amount",
        )
    }


def _parse_date_string(text: str) -> date | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    parsed = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.notna(parsed):
        return parsed.date()
    return None


class ParseError(Exception):
    pass


class StatementParser:
    EMPTY_MARKERS = (
        "there are no transactions",
        "no transactions to export",
        "money brought forward",
        "money carried forward",
    )

    def parse_file(
        self,
        content: bytes,
        filename: str,
        bank_name: str | None = None,
        statement_currency: str | None = None,
    ) -> list[ParsedTransaction]:
        bank_key = normalize_bank_key(bank_name or detect_bank_from_filename(filename))
        if bank_key == "revolut_savings":
            return []

        preset = get_preset(bank_key)
        df = self._load_dataframe(content, filename, preset)
        if df.empty:
            return []

        mapper = ColumnMapper(preset, list(df.columns))
        errors = mapper.validate()
        if errors:
            raise ParseError(f"Cannot parse {filename}: {', '.join(errors)}")

        fallback_currency = (statement_currency or preset.default_currency).upper()[:3]
        transactions: list[ParsedTransaction] = []
        for _, row in df.iterrows():
            mapped = mapper.map_row(row)
            try:
                tx = self._row_to_transaction(mapped, preset, fallback_currency)
                if tx:
                    transactions.append(tx)
            except (ValueError, InvalidOperation):
                continue
        return transactions

    def _load_dataframe(self, content: bytes, filename: str, preset: BankPreset) -> pd.DataFrame:
        ext = filename.rsplit(".", 1)[-1].lower()
        buf = io.BytesIO(content)

        if ext == "xlsx":
            raw = pd.read_excel(buf, header=None, dtype=str)
        else:
            raw = pd.read_excel(buf, header=None, dtype=str, engine="xlrd")

        # CSV embedded in single cell (HSBC LOAN, CapitalOnTap, some Revolut exports)
        if self._is_csv_blob(raw):
            return self._parse_csv_blob(raw)

        header_idx = self._find_header_row(raw, preset)
        if header_idx is None:
            raise ParseError(f"Cannot find header row in {filename}")

        if ext == "xlsx":
            df = pd.read_excel(io.BytesIO(content), header=header_idx, dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(content), header=header_idx, dtype=str, engine="xlrd")

        df.columns = [str(c).strip() for c in df.columns]
        skip = {_normalize_col(c) for c in preset.skip_columns}
        keep = [c for c in df.columns if _normalize_col(c) not in skip]
        df = df[keep]
        df = df.dropna(how="all")
        return df

    @staticmethod
    def _is_csv_blob(raw: pd.DataFrame) -> bool:
        if raw.shape[1] != 1:
            return False
        first = str(raw.iloc[0, 0])
        return "," in first and any(
            kw in first.lower() for kw in ("date", "description", "amount", "clearance")
        )

    @staticmethod
    def _parse_csv_blob(raw: pd.DataFrame) -> pd.DataFrame:
        lines = [str(raw.iloc[i, 0]) for i in range(len(raw))]
        text = "\n".join(lines)
        df = pd.read_csv(io.StringIO(text), dtype=str)
        df = df.dropna(how="all")
        return df

    def _find_header_row(self, raw: pd.DataFrame, preset: BankPreset) -> int | None:
        keywords = _header_keywords(preset)
        best_idx = None
        best_score = 0
        for i in range(min(15, len(raw))):
            row_vals = [_normalize_col(v) for v in raw.iloc[i].tolist() if pd.notna(v)]
            score = sum(1 for v in row_vals if v in keywords or any(k in v for k in keywords))
            if score > best_score:
                best_score = score
                best_idx = i
        return best_idx if best_score >= MIN_HEADER_KEYWORD_SCORE else None

    def _row_to_transaction(
        self,
        mapped: dict[str, Any],
        preset: BankPreset,
        fallback_currency: str,
    ) -> ParsedTransaction | None:
        desc = self._build_description(mapped)
        if not desc:
            return None
        if any(marker in desc.lower() for marker in self.EMPTY_MARKERS):
            return None

        tx_date = self._parse_date(mapped.get("date"))
        if tx_date is None:
            return None

        posting_date = self._parse_date(mapped.get("posting_date"))
        amount, direction = self._parse_amount(mapped)
        if amount is None or amount == 0:
            return None

        currency = self._clean_str(mapped.get("currency")) or fallback_currency
        currency = currency.upper()[:3] if currency else fallback_currency
        merchant = self._clean_str(mapped.get("merchant"))

        return ParsedTransaction(
            transaction_date=tx_date,
            posting_date=posting_date,
            description_raw=desc,
            amount=abs(amount),
            currency=currency,
            direction=direction,
            merchant_name=merchant,
        )

    def _build_description(self, mapped: dict[str, Any]) -> str | None:
        desc = self._clean_str(mapped.get("description"))
        tx_type = self._clean_str(mapped.get("type"))
        if tx_type:
            return f"{tx_type} | {desc}" if desc else tx_type
        return desc

    @staticmethod
    def _clean_str(value: Any) -> str | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip()
        return text if text and text.lower() != "nan" else None

    def _parse_date(self, value: Any) -> date | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

        text = str(value).strip()
        if not text or text.lower() == "nan":
            return None

        if " " in text and re.match(r"\d{4}-\d{2}-\d{2}", text):
            text = text.split(" ")[0]

        return _parse_date_string(text)

    def _parse_amount(self, mapped: dict[str, Any]) -> tuple[Decimal | None, str]:
        if "amount" in mapped and mapped["amount"] is not None:
            amount = self._to_decimal(mapped["amount"])
            if amount is None:
                return None, TransactionDirection.DEBIT.value
            direction = (
                TransactionDirection.CREDIT.value
                if amount > 0
                else TransactionDirection.DEBIT.value
            )
            return amount, direction

        debit = self._to_decimal(mapped.get("debit"))
        credit = self._to_decimal(mapped.get("credit"))

        if debit is not None and debit != 0:
            return -abs(debit), TransactionDirection.DEBIT.value
        if credit is not None and credit != 0:
            return abs(credit), TransactionDirection.CREDIT.value
        return None, TransactionDirection.DEBIT.value

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        text = str(value).strip().replace(",", "").replace("£", "").replace("$", "").replace("€", "")
        # Handle encoding artifacts like \ufffd
        text = re.sub(r"[^\d.\-+]", "", text)
        if not text or text in INVALID_DECIMAL_TOKENS:
            return None
        try:
            return Decimal(text)
        except InvalidOperation:
            return None
