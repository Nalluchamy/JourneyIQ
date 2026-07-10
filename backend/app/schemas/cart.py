from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductRead


class CartItemRead(BaseModel):
    """Cart Item read schema including catalog product details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    quantity: int
    product: ProductRead


class CartItemCreate(BaseModel):
    """Cart Item create payload schema."""

    product_id: int
    quantity: int = Field(1, ge=1, description="Quantity to add (must be at least 1)")


class CartItemUpdate(BaseModel):
    """Cart Item update payload schema."""

    quantity: int = Field(..., ge=1, description="Set new quantity (must be at least 1)")
