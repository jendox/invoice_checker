from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])
export_service = ExportService()


@router.get("/invoice-requests.xlsx")
async def export_invoice_requests(db: AsyncSession = Depends(get_db)) -> Response:
    content = await export_service.export_invoice_requests_xlsx(db)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="invoice-requests.xlsx"'},
    )
