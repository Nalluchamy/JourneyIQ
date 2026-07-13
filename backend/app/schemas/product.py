import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class ProductImageRead(BaseModel):
    """ProductImage response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    image_url: str
    display_order: int
    image_type: str
    alt_text: str | None = None


class ProductVariantRead(BaseModel):
    """ProductVariant response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku: str
    color: str | None = None
    storage: str | None = None
    ram: str | None = None
    price: Decimal
    stock: int
    barcode: str | None = None
    is_active: bool


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

    # Normalized Details
    sku: str | None = None
    barcode: str | None = None
    warranty: str | None = None
    seller: str | None = None
    shipping_time: str | None = None
    specifications: dict[str, Any] | None = None

    # SEO Metadata
    seo_title: str | None = None
    meta_description: str | None = None
    keywords: str | None = None
    alt_text: str | None = None

    # Badges, Availability & Pricing Metadata
    badge: str | None = None
    availability_status: str | None = None
    mrp: Decimal | None = None
    discount_percent: int | None = None
    savings: Decimal | None = None

    # AI Metadata
    sentiment_score: float | None = None
    popularity_score: float | None = None
    trend_score: float | None = None
    embedding_vector_id: str | None = None

    # Relationships
    variants: list[ProductVariantRead] = []
    images: list[ProductImageRead] = []

    @model_validator(mode="before")
    @classmethod
    def check_relationships(cls, data: Any) -> Any:
        """Pre-validator to safely default lazy-loaded relationships to avoid MissingGreenlet."""
        if hasattr(data, "__dict__"):
            # Return a dict copy to avoid modifying the SQLAlchemy object state
            d = {k: v for k, v in data.__dict__.items() if not k.startswith("_sa_")}
            if "variants" not in d:
                d["variants"] = []
            if "images" not in d:
                d["images"] = []
            return d
        return data
