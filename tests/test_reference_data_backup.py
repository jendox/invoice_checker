import json
from pathlib import Path

import pytest
from sqlalchemy import delete

from app.models.category import Category
from app.models.invoice_owner import InvoiceOwner
from app.models.vendor import Vendor
from app.schemas.category import CategoryCreate
from app.schemas.invoice_owner import InvoiceOwnerCreate
from app.schemas.vendor import VendorCreate
from app.services.category_service import CategoryService
from app.services.invoice_owner_service import InvoiceOwnerService
from app.services.reference_data_backup import (
    export_reference_data,
    read_backup_file,
    restore_reference_data,
    write_backup_file,
)
from app.services.vendor_service import VendorService


@pytest.mark.asyncio
async def test_export_restore_roundtrip(session, tmp_path: Path):
    await CategoryService().create(
        session,
        CategoryCreate(slug="marketing", label="Marketing", badge_bg="#111111", badge_text="#eeeeee"),
    )
    await InvoiceOwnerService().create(session, InvoiceOwnerCreate(name="Backup Owner", email="a@example.com"))
    await VendorService().create(
        session,
        VendorCreate(name="Backup Vendor", aliases=["bv"], default_category="marketing"),
    )

    payload = await export_reference_data(session)
    backup_path = tmp_path / "reference_data.json"
    write_backup_file(backup_path, payload)

    await session.execute(delete(Vendor))
    await session.execute(delete(InvoiceOwner))
    await session.execute(delete(Category).where(Category.slug == "marketing"))
    await session.commit()

    restored = read_backup_file(backup_path)
    stats = await restore_reference_data(session, restored)

    assert stats.categories >= 1
    assert stats.vendors == 1
    assert stats.invoice_owners >= 1

    payload_after = await export_reference_data(session)
    assert payload_after["categories"] == payload["categories"]
    assert payload_after["vendors"] == payload["vendors"]


@pytest.mark.asyncio
async def test_backup_file_is_valid_json(session, tmp_path: Path):
    payload = await export_reference_data(session)
    path = tmp_path / "reference_data.json"
    write_backup_file(path, payload)

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["version"] == 1
    assert "categories" in loaded
