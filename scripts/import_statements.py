#!/usr/bin/env python3
"""Bulk-import statement files from statements/{company}/ folders."""

import asyncio
import sys
from datetime import date
from pathlib import Path

from app.database import async_session_factory
from app.services.parser.bank_presets import detect_bank_from_filename, detect_currency_from_filename
from app.services.transaction_service import TransactionService

STATEMENT_EXTENSIONS = {".xls", ".xlsx", ".csv"}


async def main(month: str) -> None:
    base = Path(__file__).resolve().parent.parent / "statements"
    if not base.exists():
        print(f"No statements directory at {base}")
        sys.exit(1)

    service = TransactionService()
    total_imported = 0
    total_review = 0
    total_invoice = 0

    async with async_session_factory() as session:
        for company_dir in sorted(base.iterdir()):
            if not company_dir.is_dir():
                continue
            company = company_dir.name
            for path in sorted(company_dir.iterdir()):
                if path.suffix.lower() not in STATEMENT_EXTENSIONS:
                    continue
                bank = detect_bank_from_filename(path.name)
                currency = detect_currency_from_filename(path.name)
                try:
                    result = await service.upload_statement(
                        session,
                        path.read_bytes(),
                        path.name,
                        bank,
                        month,
                        company,
                        currency,
                    )
                    total_imported += result.imported_count
                    total_review += result.needs_review_count
                    total_invoice += result.requires_invoice_count
                    print(
                        f"{company}/{path.name}: "
                        f"+{result.imported_count} imported, "
                        f"{result.skipped_duplicates} skipped, "
                        f"review={result.needs_review_count}, "
                        f"invoice={result.requires_invoice_count}",
                    )
                except ValueError as e:
                    print(f"{company}/{path.name}: SKIP — {e}")

    print(f"\nDone: {total_imported} imported, {total_review} need review, {total_invoice} need invoice")


if __name__ == "__main__":
    month = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime("%Y-%m")
    asyncio.run(main(month))
