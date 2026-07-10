from pydantic import BaseModel, ConfigDict

from app.schemas.product import ProductRead


class WishlistItemRead(BaseModel):
    """Wishlist Item read schema including catalog product details."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    product: ProductRead


class WishlistItemCreate(BaseModel):
    """Wishlist Item create payload schema."""

    product_id: int
