from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.inventory_history import InventoryHistory
    from app.models.order_item import OrderItem
    from app.models.recommendation import Recommendation
    from app.models.review import Review
    from app.models.product_variant import ProductVariant
    from app.models.product_image import ProductImage


class Product(BaseModel, SoftDeleteMixin):
    """Product DB Model."""

    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, server_default="true", nullable=False
    )

    # Normalized Details
    sku: Mapped[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    warranty: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seller: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    specifications: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # SEO Metadata
    seo_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    keywords: Mapped[str | None] = mapped_column(String(255), nullable=True)
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Badges, Availability & Pricing Metadata
    badge: Mapped[str | None] = mapped_column(String(50), nullable=True)
    availability_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mrp: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    discount_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    savings: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # AI Metadata
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    popularity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    trend_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    embedding_vector_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_product_price_non_negative"),
        CheckConstraint("stock >= 0", name="check_product_stock_non_negative"),
    )

    # Relationships
    category: Mapped["Category"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product", cascade="all, delete"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    inventory_history: Mapped[list["InventoryHistory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
