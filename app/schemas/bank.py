from pydantic import BaseModel, ConfigDict, Field


class BankCreate(BaseModel):
    key: str = Field(min_length=1, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    default_currency: str = Field(default="GBP", min_length=3, max_length=3)
    is_active: bool = True


class BankUpdate(BaseModel):
    key: str | None = None
    display_name: str | None = None
    default_currency: str | None = None
    is_active: bool | None = None


class BankRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    display_name: str
    default_currency: str
    is_active: bool
