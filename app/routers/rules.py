from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.rule import RuleCreate, RuleRead, RuleUpdate
from app.services.rule_service import RuleService

router = APIRouter(prefix="/rules", tags=["rules"])
rule_service = RuleService()


@router.get("", response_model=list[RuleRead])
async def list_rules(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[RuleRead]:
    rules = await rule_service.list_rules(db, active_only=active_only)
    return [RuleRead.model_validate(r) for r in rules]


@router.post("", response_model=RuleRead, status_code=201)
async def create_rule(data: RuleCreate, db: AsyncSession = Depends(get_db)) -> RuleRead:
    rule = await rule_service.create_rule(db, data)
    return RuleRead.model_validate(rule)


@router.patch("/{rule_id}", response_model=RuleRead)
async def update_rule(
    rule_id: int, data: RuleUpdate, db: AsyncSession = Depends(get_db),
) -> RuleRead:
    try:
        rule = await rule_service.update_rule(db, rule_id, data)
        return RuleRead.model_validate(rule)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await rule_service.delete_rule(db, rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/{rule_id}/deactivate", response_model=RuleRead)
async def deactivate_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> RuleRead:
    try:
        rule = await rule_service.deactivate_rule(db, rule_id)
        return RuleRead.model_validate(rule)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
