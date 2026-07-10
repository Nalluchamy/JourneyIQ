from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class CartItem(BaseModel):
    """CartItem DB Model."""

    __tablename__ = "cartitem"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", product_id, name="uq_cart_user_product"),
        CheckConstraint("quantity > 0", name="check_cart_item_quantity_positive"),
    )
