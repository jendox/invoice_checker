from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StatementUploadResponse(BaseModel):
    statement_file_id: int
    bank_name: str
    company_name: str | None
    statement_month: str
    currency: str
    original_filename: str
    imported_count: int
    skipped_duplicates: int
    needs_review_count: int
    requires_invoice_count: int


class StatementFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_name: str
    company_name: str | None
    statement_month: str
    currency: str
    original_filename: str
    uploaded_at: datetime
