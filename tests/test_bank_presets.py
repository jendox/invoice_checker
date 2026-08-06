from decimal import Decimal
from pathlib import Path

import pytest

from app.services.parser.bank_presets import (
    detect_bank_from_filename,
    detect_currency_from_filename,
    normalize_bank_key,
)
from app.services.parser.statement_parser import StatementParser

REVOLUT_FILE = Path(__file__).resolve().parent.parent / "statements" / "hipcrate" / "+Revolut£ 1-30.06.26.xls"


def test_normalize_bank_key_merges_legacy_keys():
    assert normalize_bank_key("amex_gbp") == "amex"
    assert normalize_bank_key("amex_usd") == "amex"
    assert normalize_bank_key("hsbc_gbp") == "hsbc"
    assert normalize_bank_key("paypal") == "paypal"


def test_detect_bank_from_filename_no_currency_suffix():
    assert detect_bank_from_filename("+Amex$ 1-30.06.26.xlsx") == "amex"
    assert detect_bank_from_filename("+HSBC$ 1-30.06.26.xls") == "hsbc"


def test_detect_currency_from_filename():
    assert detect_currency_from_filename("+Amex£ 1-30.06.26.xlsx") == "GBP"
    assert detect_currency_from_filename("+Amex$ 1-30.06.26.xlsx") == "USD"
    assert detect_currency_from_filename("+HSBC USD 1-30.06.26.xls") == "USD"


@pytest.fixture
def revolut_transactions():
    if not REVOLUT_FILE.exists():
        pytest.skip(f"File not found: {REVOLUT_FILE}")
    content = REVOLUT_FILE.read_bytes()
    return StatementParser().parse_file(content, REVOLUT_FILE.name, "revolut")


def test_revolut_uses_orig_currency_amount(revolut_transactions):
    fiverr = next(tx for tx in revolut_transactions if "Fiverr" in tx.description_raw)
    assert fiverr.amount == Decimal("40.43")
    assert fiverr.currency == "USD"

    gocardless = next(tx for tx in revolut_transactions if tx.description_raw == "Gocardless")
    assert gocardless.amount == Decimal("81")
    assert gocardless.currency == "GBP"
