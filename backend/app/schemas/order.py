import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrderItemRead(BaseModel):
    """OrderItem nested response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderStatusHistoryRead(BaseModel):
    """OrderStatusHistory nested response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    status: str
    notes: str | None = None
    created_at: datetime.datetime


class OrderRead(BaseModel):
    """Order response schema with items list and history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    invoice_number: str | None = None
    shipping_address_id: int | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: list[OrderItemRead] = []
    status_history: list[OrderStatusHistoryRead] = []


class CheckoutRequest(BaseModel):
    """Checkout request payload schema."""

    shipping_address_id: int
    coupon_code: str | None = None


class CheckoutResponse(BaseModel):
    """Checkout success response schema."""

    order_id: int
    invoice_number: str
    payment_status: str


class CartSummaryResponse(BaseModel):
    """Cart price summary response schema."""

    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    discount: Decimal
    grand_total: Decimal

