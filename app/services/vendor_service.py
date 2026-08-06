from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate


class VendorService:
    async def list_vendors(self, session: AsyncSession) -> list[Vendor]:
        result = await session.execute(select(Vendor).order_by(Vendor.name))
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, data: VendorCreate) -> Vendor:
        vendor = Vendor(
            name=data.name,
            normalized_name=data.name.lower().strip(),
            aliases=data.aliases,
            default_category=data.default_category,
            default_requires_invoice=data.default_requires_invoice,
            default_invoice_provider=data.default_invoice_provider,
            default_invoice_owner=data.default_invoice_owner,
            notes=data.notes,
        )
        session.add(vendor)
        await session.commit()
        await session.refresh(vendor)
        return vendor

    async def update(self, session: AsyncSession, vendor_id: int, data: VendorUpdate) -> Vendor:
        vendor = await self._get_or_raise(session, vendor_id)
        updates = data.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] is not None:
            vendor.normalized_name = updates["name"].lower().strip()
        for key, value in updates.items():
            setattr(vendor, key, value)
        await session.commit()
        await session.refresh(vendor)
        return vendor

    async def delete(self, session: AsyncSession, vendor_id: int) -> None:
        vendor = await self._get_or_raise(session, vendor_id)
        await session.delete(vendor)
        await session.commit()

    async def _get_or_raise(self, session: AsyncSession, vendor_id: int) -> Vendor:
        result = await session.execute(select(Vendor).where(Vendor.id == vendor_id))
        vendor = result.scalar_one_or_none()
        if vendor is None:
            raise ValueError(f"Vendor {vendor_id} not found")
        return vendor
