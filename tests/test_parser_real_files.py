from pathlib import Path

import pytest

from app.services.parser.statement_parser import StatementParser

STATEMENTS_DIR = Path(__file__).resolve().parent.parent / "statements"


@pytest.mark.parametrize(
    "rel_path,bank",
    [
        ("cubetag/+Amex£ 1-30.06.26.xlsx", "amex"),
        ("cubetag/+HSBC£ 1-30.06.26.xls", "hsbc"),
        ("doorz/+Revolut £ 1-30.06.2026.xls", "revolut"),
        ("doorz/+Barclays 13.05-12.06.26.xlsx", "barclays"),
        ("cubetag/+HSBC LOAN £1-30.06.26.xls", "hsbc_csv"),
        ("hipcrate/+PayPal 1-30.06.26.xlsx", "paypal"),
    ],
)
def test_parse_real_statements(rel_path, bank):
    path = STATEMENTS_DIR / rel_path
    if not path.exists():
        pytest.skip(f"File not found: {path}")

    content = path.read_bytes()
    parser = StatementParser()
    txs = parser.parse_file(content, path.name, bank)
    assert len(txs) > 0, f"No transactions parsed from {rel_path}"
    assert all(tx.description_raw for tx in txs)
    assert all(tx.amount > 0 for tx in txs)
