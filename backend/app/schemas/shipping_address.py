import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShippingAddressBase(BaseModel):
    full_name: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=20)
    address_line1: str = Field(..., max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    country: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=20)
    is_default: bool = False


class ShippingAddressCreate(ShippingAddressBase):
    pass


class ShippingAddressUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=20)
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=20)
    is_default: bool | None = None


class ShippingAddressRead(ShippingAddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
