from pydantic import BaseModel, ConfigDict, Field


class InvoiceOwnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str | None = None
    notes: str | None = None
    is_active: bool = True


class InvoiceOwnerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class InvoiceOwnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None
    notes: str | None
    is_active: bool
