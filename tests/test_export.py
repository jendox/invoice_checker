from datetime import date
from decimal import Decimal

import pytest

from app.models.statement_file import StatementFile
from app.models.transaction import Transaction
from app.services.export_service import ExportService


@pytest.mark.asyncio
async def test_xlsx_export_generation(session):
    stmt = StatementFile(
        bank_name="amex",
        company_name="hipcrate",
        statement_month="2026-06",
        original_filename="test.xlsx",
    )
    session.add(stmt)
    await session.flush()

    session.add(
        Transaction(
            statement_file_id=stmt.id,
            bank_name="amex",
            transaction_date=date(2026, 6, 1),
            description_raw="GOOGLE ADS",
            description_normalized="google ads",
            amount=Decimal("500.00"),
            currency="GBP",
            direction="debit",
            category="software_subscription",
            requires_invoice=True,
            invoice_provider="Google",
            confidence=Decimal("0.75"),
            classification_source="rule",
            status="new",
            fingerprint="def456" + "0" * 58,
        ),
    )
    await session.commit()

    service = ExportService()
    content = await service.export_invoice_requests_xlsx(session)

    assert len(content) > 0
    assert content[:2] == b"PK"  # XLSX is a zip file

    import io

    import pandas as pd

    df = pd.read_excel(io.BytesIO(content))
    assert len(df) == 1
    assert df.iloc[0]["Description"] == "GOOGLE ADS"
    assert df.iloc[0]["Invoice Provider"] == "Google"
