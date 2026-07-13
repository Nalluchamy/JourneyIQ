from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.product import Product


class ProductImage(BaseModel):
    """ProductImage DB Model."""

    __tablename__ = "product_image"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(255), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_type: Mapped[str] = mapped_column(String(50), nullable=False)  # hero, front, side, lifestyle, feature
    alt_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="images")
