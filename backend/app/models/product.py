from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.inventory_history import InventoryHistory
    from app.models.order_item import OrderItem
    from app.models.recommendation import Recommendation
    from app.models.review import Review


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
