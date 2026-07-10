import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    """Product response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    slug: str
    description: str | None = None
    brand: str | None = None
    image_url: str | None = None
    price: Decimal
    stock: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
