from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.product import Product


class InventoryHistory(BaseModel):
    """Inventory History Ledger DB Model."""

    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True
    )
    old_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    new_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        CheckConstraint("old_stock >= 0", name="check_old_stock_non_negative"),
        CheckConstraint("new_stock >= 0", name="check_new_stock_non_negative"),
    )

    # Relationships
    product: Mapped["Product"] = relationship(back_populates="inventory_history")
