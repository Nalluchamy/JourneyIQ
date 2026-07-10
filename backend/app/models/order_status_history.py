from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.order import Order


class OrderStatusHistory(BaseModel):
    """OrderStatusHistory DB Model."""

    __tablename__ = "orderstatushistory"

    order_id: Mapped[int] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="status_history")
