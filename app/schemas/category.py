from pydantic import BaseModel, ConfigDict, Field

from app.utils.category_colors import DEFAULT_BADGE_BG, DEFAULT_BADGE_TEXT


class CategoryCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=50)
    label: str = Field(min_length=1, max_length=100)
    sort_order: int = 100
    requires_invoice_default: bool | None = None
    is_active: bool = True
    badge_bg: str = Field(default=DEFAULT_BADGE_BG, pattern=r"^#[0-9A-Fa-f]{6}$")
    badge_text: str = Field(default=DEFAULT_BADGE_TEXT, pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryUpdate(BaseModel):
    slug: str | None = None
    label: str | None = None
    sort_order: int | None = None
    requires_invoice_default: bool | None = None
    is_active: bool | None = None
    badge_bg: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    badge_text: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    sort_order: int
    is_active: bool
    requires_invoice_default: bool | None
    badge_bg: str
    badge_text: str
