"""Export/import reference data (everything except transactions and related rows)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank import Bank
from app.models.category import Category
from app.models.classification_rule import ClassificationRule
from app.models.company import Company
from app.models.invoice_owner import InvoiceOwner
from app.models.vendor import Vendor

BACKUP_VERSION = 1
DEFAULT_BACKUP_PATH = Path(__file__).resolve().parents[2] / "data" / "reference_data.json"


@dataclass
class RestoreStats:
    categories: int = 0
    banks: int = 0
    companies: int = 0
    invoice_owners: int = 0
    vendors: int = 0
    classification_rules: int = 0


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _model_to_dict(instance: Any, *, exclude: set[str] | None = None) -> dict[str, Any]:
    skip = exclude or {"id"}
    return {
        column.name: _serialize_value(getattr(instance, column.name))
        for column in instance.__table__.columns
        if column.name not in skip
    }


async def export_reference_data(session: AsyncSession) -> dict[str, Any]:
    categories = list((await session.execute(select(Category).order_by(Category.sort_order, Category.slug))).scalars())
    banks = list((await session.execute(select(Bank).order_by(Bank.key))).scalars())
    companies = list((await session.execute(select(Company).order_by(Company.key))).scalars())
    invoice_owners = list(
        (await session.execute(select(InvoiceOwner).order_by(InvoiceOwner.name))).scalars(),
    )
    vendors = list((await session.execute(select(Vendor).order_by(Vendor.name))).scalars())
    rules = list(
        (
            await session.execute(
                select(ClassificationRule).order_by(
                    ClassificationRule.priority.desc(),
                    ClassificationRule.name,
                    ClassificationRule.pattern,
                ),
            )
        ).scalars(),
    )

    return {
        "version": BACKUP_VERSION,
        "exported_at": datetime.now(UTC).isoformat(),
        "categories": [_model_to_dict(row) for row in categories],
        "banks": [_model_to_dict(row) for row in banks],
        "companies": [_model_to_dict(row) for row in companies],
        "invoice_owners": [_model_to_dict(row) for row in invoice_owners],
        "vendors": [_model_to_dict(row) for row in vendors],
        "classification_rules": [_model_to_dict(row, exclude={"id", "created_at"}) for row in rules],
    }


def write_backup_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_backup_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != BACKUP_VERSION:
        raise ValueError(f"Unsupported backup version: {payload.get('version')!r}")
    return payload


async def _sync_keyed_rows(
    session: AsyncSession,
    model: type[Any],
    key_field: str,
    rows: list[dict[str, Any]],
) -> int:
    backup_keys = {row[key_field] for row in rows}
    existing = list((await session.execute(select(model))).scalars())
    for item in existing:
        if getattr(item, key_field) not in backup_keys:
            await session.delete(item)

    count = 0
    for row in rows:
        result = await session.execute(select(model).where(getattr(model, key_field) == row[key_field]))
        item = result.scalar_one_or_none()
        if item is None:
            session.add(model(**row))
        else:
            for field, value in row.items():
                setattr(item, field, value)
        count += 1
    return count


async def restore_reference_data(session: AsyncSession, payload: dict[str, Any]) -> RestoreStats:
    stats = RestoreStats()

    stats.categories = await _sync_keyed_rows(session, Category, "slug", payload.get("categories", []))
    stats.banks = await _sync_keyed_rows(session, Bank, "key", payload.get("banks", []))
    stats.companies = await _sync_keyed_rows(session, Company, "key", payload.get("companies", []))

    await session.execute(delete(ClassificationRule))
    await session.execute(delete(Vendor))
    await session.execute(delete(InvoiceOwner))

    for row in payload.get("invoice_owners", []):
        session.add(InvoiceOwner(**row))
        stats.invoice_owners += 1

    for row in payload.get("vendors", []):
        session.add(Vendor(**row))
        stats.vendors += 1

    for row in payload.get("classification_rules", []):
        session.add(ClassificationRule(**row))
        stats.classification_rules += 1

    await session.commit()
    return stats
