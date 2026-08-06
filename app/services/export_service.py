import io

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.statement_file import StatementFile
from app.models.transaction import Transaction


class ExportService:
    async def export_invoice_requests_xlsx(self, session: AsyncSession) -> bytes:
        result = await session.execute(
            select(Transaction, StatementFile)
            .join(StatementFile, Transaction.statement_file_id == StatementFile.id)
            .where(Transaction.requires_invoice.is_(True))
            .order_by(Transaction.transaction_date.desc()),
        )
        rows = result.all()

        data = []
        for tx, stmt in rows:
            data.append(
                {
                    "Date": tx.transaction_date.isoformat(),
                    "Company": stmt.company_name or "",
                    "Bank": tx.bank_name,
                    "Description": tx.description_raw,
                    "Merchant": tx.merchant_name or "",
                    "Amount": float(tx.amount),
                    "Currency": tx.currency,
                    "Direction": tx.direction,
                    "Category": tx.category,
                    "Invoice Provider": tx.invoice_provider or "",
                    "Invoice Owner": tx.invoice_owner or "",
                    "Confidence": float(tx.confidence),
                    "Status": tx.status,
                    "Statement Month": stmt.statement_month,
                },
            )

        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Invoice Requests")
        buffer.seek(0)
        return buffer.getvalue()
