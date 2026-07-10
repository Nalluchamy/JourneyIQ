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


class OrderRead(BaseModel):
    """Order response schema with items list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    created_at: datetime.datetime
    updated_at: datetime.datetime
    items: list[OrderItemRead] = []
