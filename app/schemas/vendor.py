from pydantic import BaseModel, ConfigDict, Field


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    aliases: list[str] = Field(default_factory=list)
    default_category: str | None = None
    default_requires_invoice: bool | None = None
    default_invoice_provider: str | None = None
    default_invoice_owner: str | None = None
    notes: str | None = None


class VendorUpdate(BaseModel):
    name: str | None = None
    aliases: list[str] | None = None
    default_category: str | None = None
    default_requires_invoice: bool | None = None
    default_invoice_provider: str | None = None
    default_invoice_owner: str | None = None
    notes: str | None = None


class VendorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    normalized_name: str
    aliases: list
    default_category: str | None
    default_requires_invoice: bool | None
    default_invoice_provider: str | None
    default_invoice_owner: str | None
    notes: str | None
