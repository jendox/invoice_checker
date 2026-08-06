from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.statement import StatementUploadResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/statements", tags=["statements"])
service = TransactionService()

ALLOWED_UPLOAD_EXTENSIONS = {"csv", "xlsx", "xls"}


@router.post("/upload", response_model=StatementUploadResponse)
async def upload_statement(
    file: UploadFile = File(...),
    bank_name: str = Form(...),
    statement_month: str = Form(..., pattern=r"^\d{4}-\d{2}$"),
    statement_currency: str = Form("GBP"),
    company_name: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
) -> StatementUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, XLSX, or XLS.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        return await service.upload_statement(
            db,
            content,
            file.filename,
            bank_name,
            statement_month,
            company_name,
            statement_currency.strip().upper()[:3],
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
