from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.deps import TransactionFiltersDep
from app.schemas.transaction import (
    ClassificationUpdate,
    DeleteTransactionsRequest,
    DeleteTransactionsResponse,
    ReclassifyRequest,
    ReclassifyResponse,
    TransactionListResponse,
    TransactionRead,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])
service = TransactionService()


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    filters: TransactionFiltersDep,
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    items, total = await service.list_transactions(db, filters)
    return TransactionListResponse(
        items=[TransactionRead.model_validate(i) for i in items],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=service.paginate(total, filters.page, filters.page_size),
    )


@router.patch("/{transaction_id}/classification", response_model=TransactionRead)
async def update_classification(
    transaction_id: int,
    update: ClassificationUpdate,
    db: AsyncSession = Depends(get_db),
) -> TransactionRead:
    try:
        tx = await service.update_classification(db, transaction_id, update)
        return TransactionRead.model_validate(tx)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/reclassify", response_model=ReclassifyResponse)
async def reclassify_transactions(
    options: ReclassifyRequest,
    db: AsyncSession = Depends(get_db),
) -> ReclassifyResponse:
    updated, skipped = await service.reclassify_transactions(db, options)
    return ReclassifyResponse(updated=updated, skipped=skipped)


@router.post("/delete", response_model=DeleteTransactionsResponse)
async def delete_transactions(
    options: DeleteTransactionsRequest,
    db: AsyncSession = Depends(get_db),
) -> DeleteTransactionsResponse:
    deleted = await service.delete_transactions(db, options)
    return DeleteTransactionsResponse(deleted=deleted)


@router.get("/invoice-requests", response_model=list[TransactionRead])
async def invoice_requests(db: AsyncSession = Depends(get_db)) -> list[TransactionRead]:
    items = await service.get_invoice_requests(db)
    return [TransactionRead.model_validate(i) for i in items]
