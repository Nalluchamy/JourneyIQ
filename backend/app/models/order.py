from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.coupon_usage import CouponUsage
    from app.models.order_item import OrderItem
    from app.models.order_status_history import OrderStatusHistory
    from app.models.payment import Payment
    from app.models.shipping_address import ShippingAddress
    from app.models.user import User


class Order(BaseModel):
    """Order DB Model."""

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending", server_default="pending", nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), server_default="0.00", nullable=False
    )
    discount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), server_default="0.00", nullable=False
    )
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    invoice_number: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    shipping_address_id: Mapped[int | None] = mapped_column(
        ForeignKey("shippingaddress.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="check_order_subtotal_non_negative"),
        CheckConstraint("tax >= 0", name="check_order_tax_non_negative"),
        CheckConstraint("discount >= 0", name="check_order_discount_non_negative"),
        CheckConstraint("total >= 0", name="check_order_total_non_negative"),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    shipping_address: Mapped["ShippingAddress | None"] = relationship()
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    coupon_usages: Mapped[list["CouponUsage"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
