from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.order import Order


class Payment(BaseModel):
    """Payment Transaction DB Model."""

    order_id: Mapped[int] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10), default="USD", server_default="USD", nullable=False
    )

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_payment_amount_non_negative"),
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="payments")
