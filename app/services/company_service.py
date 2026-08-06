from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company


class CompanyService:
    async def list_companies(self, session: AsyncSession, active_only: bool = True) -> list[Company]:
        stmt = select(Company).order_by(Company.display_name)
        if active_only:
            stmt = stmt.where(Company.is_active.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())
