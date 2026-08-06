from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice_owner import InvoiceOwner
from app.models.transaction import Transaction
from app.schemas.invoice_owner import InvoiceOwnerCreate, InvoiceOwnerUpdate


class InvoiceOwnerService:
    async def list_owners(
        self, session: AsyncSession, active_only: bool = False,
    ) -> list[InvoiceOwner]:
        stmt = select(InvoiceOwner).order_by(InvoiceOwner.name)
        if active_only:
            stmt = stmt.where(InvoiceOwner.is_active.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, data: InvoiceOwnerCreate) -> InvoiceOwner:
        owner = InvoiceOwner(**data.model_dump())
        session.add(owner)
        await session.commit()
        await session.refresh(owner)
        return owner

    async def update(
        self, session: AsyncSession, owner_id: int, data: InvoiceOwnerUpdate,
    ) -> InvoiceOwner:
        owner = await self._get_or_raise(session, owner_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(owner, key, value)
        await session.commit()
        await session.refresh(owner)
        return owner

    async def delete(self, session: AsyncSession, owner_id: int) -> None:
        owner = await self._get_or_raise(session, owner_id)
        in_use = (
            await session.execute(
                select(func.count(Transaction.id)).where(Transaction.invoice_owner == owner.name),
            )
        ).scalar_one()
        if in_use:
            owner.is_active = False
            await session.commit()
            return
        await session.delete(owner)
        await session.commit()

    async def _get_or_raise(self, session: AsyncSession, owner_id: int) -> InvoiceOwner:
        result = await session.execute(select(InvoiceOwner).where(InvoiceOwner.id == owner_id))
        owner = result.scalar_one_or_none()
        if owner is None:
            raise ValueError(f"Invoice owner {owner_id} not found")
        return owner
