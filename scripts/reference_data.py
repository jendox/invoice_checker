#!/usr/bin/env python3
"""Export or restore reference data (categories, vendors, rules, etc.)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from app.database import async_session_factory
from app.services.reference_data_backup import (
    DEFAULT_BACKUP_PATH,
    RestoreStats,
    export_reference_data,
    read_backup_file,
    restore_reference_data,
    write_backup_file,
)


def _print_stats(stats: RestoreStats) -> None:
    print(
        "Restored: "
        f"{stats.categories} categories, "
        f"{stats.banks} banks, "
        f"{stats.companies} companies, "
        f"{stats.invoice_owners} invoice owners, "
        f"{stats.vendors} vendors, "
        f"{stats.classification_rules} rules",
    )


async def _export(path: Path) -> int:
    async with async_session_factory() as session:
        payload = await export_reference_data(session)

    write_backup_file(path, payload)
    print(f"Exported reference data to {path}")
    print(
        f"  {len(payload['categories'])} categories, "
        f"{len(payload['banks'])} banks, "
        f"{len(payload['companies'])} companies, "
        f"{len(payload['invoice_owners'])} invoice owners, "
        f"{len(payload['vendors'])} vendors, "
        f"{len(payload['classification_rules'])} rules",
    )
    return 0


async def _restore(path: Path) -> int:
    if not path.exists():
        print(f"Backup file not found: {path}", file=sys.stderr)
        return 1

    payload = read_backup_file(path)
    async with async_session_factory() as session:
        stats = await restore_reference_data(session, payload)

    _print_stats(stats)
    print(f"Loaded from {path}")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(description="Export or restore invoice-checker reference data")
    parser.add_argument("command", choices=["export", "restore"])
    parser.add_argument(
        "--file",
        "-f",
        type=Path,
        default=DEFAULT_BACKUP_PATH,
        help=f"Backup file path (default: {DEFAULT_BACKUP_PATH})",
    )
    args = parser.parse_args()

    if args.command == "export":
        return await _export(args.file)
    return await _restore(args.file)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
