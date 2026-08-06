from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.classification_rule import ClassificationRule
from app.schemas.rule import RuleCreate, RuleUpdate
from app.services.rule_service import RuleService


@pytest.mark.asyncio
async def test_update_rule(session):
    service = RuleService()
    created = await service.create_rule(
        session,
        RuleCreate(
            name="Test rule",
            pattern="acme",
            pattern_type="contains",
            category="supplier_purchase",
            requires_invoice=True,
            priority=50,
            confidence=Decimal("0.7"),
        ),
    )

    updated = await service.update_rule(
        session,
        created.id,
        RuleUpdate(name="Updated rule", priority=150, is_active=False),
    )

    assert updated.name == "Updated rule"
    assert updated.priority == 150
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_delete_rule(session):
    service = RuleService()
    created = await service.create_rule(
        session,
        RuleCreate(
            name="Delete me",
            pattern="temp",
            category="unknown",
        ),
    )

    await service.delete_rule(session, created.id)

    remaining = (
        await session.execute(select(ClassificationRule).where(ClassificationRule.id == created.id))
    ).scalar_one_or_none()
    assert remaining is None
