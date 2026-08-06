from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank import Bank
from app.models.statement_file import StatementFile
from app.schemas.bank import BankCreate, BankUpdate


class BankService:
    async def list_banks(self, session: AsyncSession, active_only: bool = False) -> list[Bank]:
        stmt = select(Bank).order_by(Bank.display_name)
        if active_only:
            stmt = stmt.where(Bank.is_active.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, data: BankCreate) -> Bank:
        bank = Bank(**data.model_dump())
        session.add(bank)
        await session.commit()
        await session.refresh(bank)
        return bank

    async def update(self, session: AsyncSession, bank_id: int, data: BankUpdate) -> Bank:
        bank = await self._get_or_raise(session, bank_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(bank, key, value)
        await session.commit()
        await session.refresh(bank)
        return bank

    async def delete(self, session: AsyncSession, bank_id: int) -> None:
        bank = await self._get_or_raise(session, bank_id)
        in_use = (
            await session.execute(
                select(func.count(StatementFile.id)).where(StatementFile.bank_name == bank.key),
            )
        ).scalar_one()
        if in_use:
            bank.is_active = False
            await session.commit()
            return
        await session.delete(bank)
        await session.commit()

    async def _get_or_raise(self, session: AsyncSession, bank_id: int) -> Bank:
        result = await session.execute(select(Bank).where(Bank.id == bank_id))
        bank = result.scalar_one_or_none()
        if bank is None:
            raise ValueError(f"Bank {bank_id} not found")
        return bank
