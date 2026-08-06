from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification_rule import ClassificationRule
from app.schemas.rule import RuleCreate, RuleUpdate


class RuleService:
    async def list_rules(self, session: AsyncSession, active_only: bool = False) -> list[ClassificationRule]:
        stmt = select(ClassificationRule).order_by(ClassificationRule.priority.desc())
        if active_only:
            stmt = stmt.where(ClassificationRule.is_active.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_rule(self, session: AsyncSession, data: RuleCreate) -> ClassificationRule:
        rule = ClassificationRule(**data.model_dump())
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule

    async def update_rule(
        self, session: AsyncSession, rule_id: int, data: RuleUpdate,
    ) -> ClassificationRule:
        result = await session.execute(select(ClassificationRule).where(ClassificationRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if rule is None:
            raise ValueError(f"Rule {rule_id} not found")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)

        await session.commit()
        await session.refresh(rule)
        return rule

    async def deactivate_rule(self, session: AsyncSession, rule_id: int) -> ClassificationRule:
        result = await session.execute(select(ClassificationRule).where(ClassificationRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if rule is None:
            raise ValueError(f"Rule {rule_id} not found")
        rule.is_active = False
        await session.commit()
        await session.refresh(rule)
        return rule

    async def delete_rule(self, session: AsyncSession, rule_id: int) -> None:
        result = await session.execute(select(ClassificationRule).where(ClassificationRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if rule is None:
            raise ValueError(f"Rule {rule_id} not found")
        await session.delete(rule)
        await session.commit()

    async def get_rule(self, session: AsyncSession, rule_id: int) -> ClassificationRule | None:
        result = await session.execute(select(ClassificationRule).where(ClassificationRule.id == rule_id))
        return result.scalar_one_or_none()
