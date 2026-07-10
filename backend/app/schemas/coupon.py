import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CouponBase(BaseModel):
    code: str = Field(..., max_length=50)
    description: str | None = None
    discount_type: str = Field(..., pattern="^(percentage|fixed)$")
    discount_value: Decimal
    minimum_order: Decimal = Decimal("0.00")
    maximum_discount: Decimal | None = None
    start_date: datetime.datetime
    expiry_date: datetime.datetime
    usage_limit: int = 0
    is_active: bool = True


class CouponRead(CouponBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CouponApplyRequest(BaseModel):
    code: str = Field(..., max_length=50)
    cart_total: Decimal


class CouponApplyResponse(BaseModel):
    code: str
    discount_type: str
    discount_value: Decimal
    discount_amount: Decimal
    is_valid: bool
    message: str
