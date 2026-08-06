
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
