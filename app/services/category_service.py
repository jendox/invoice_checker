from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.category_colors import badge_colors_for_slug


class CategoryService:
    async def list_categories(
        self, session: AsyncSession, active_only: bool = False,
    ) -> list[Category]:
        stmt = select(Category).order_by(Category.sort_order, Category.label)
        if active_only:
            stmt = stmt.where(Category.is_active.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, data: CategoryCreate) -> Category:
        payload = data.model_dump()
        if not payload.get("badge_bg") or not payload.get("badge_text"):
            bg, text = badge_colors_for_slug(data.slug)
            payload.setdefault("badge_bg", bg)
            payload.setdefault("badge_text", text)
        category = Category(**payload)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category

    async def update(
        self, session: AsyncSession, category_id: int, data: CategoryUpdate,
    ) -> Category:
        category = await self._get_or_raise(session, category_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        await session.commit()
        await session.refresh(category)
        return category

    async def delete(self, session: AsyncSession, category_id: int) -> None:
        category = await self._get_or_raise(session, category_id)
        in_use = (
            await session.execute(
                select(func.count(Transaction.id)).where(Transaction.category == category.slug),
            )
        ).scalar_one()
        if in_use:
            category.is_active = False
            await session.commit()
            return
        await session.delete(category)
        await session.commit()

    async def _get_or_raise(self, session: AsyncSession, category_id: int) -> Category:
        result = await session.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if category is None:
            raise ValueError(f"Category {category_id} not found")
        return category
