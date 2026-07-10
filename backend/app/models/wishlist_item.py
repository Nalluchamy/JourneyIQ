from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class WishlistItem(BaseModel):
    """WishlistItem DB Model."""

    __tablename__ = "wishlistitem"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", product_id, name="uq_wishlist_user_product"),
    )
