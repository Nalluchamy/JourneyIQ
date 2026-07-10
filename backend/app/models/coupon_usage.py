import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.coupon import Coupon
    from app.models.order import Order
    from app.models.user import User


class CouponUsage(BaseModel):
    """CouponUsage DB Model."""

    __tablename__ = "couponusage"

    coupon_id: Mapped[int] = mapped_column(
        ForeignKey("coupon.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("order.id", ondelete="CASCADE"), nullable=False, index=True
    )
    used_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    coupon: Mapped["Coupon"] = relationship(back_populates="usages")
    user: Mapped["User"] = relationship(back_populates="coupon_usages")
    order: Mapped["Order"] = relationship(back_populates="coupon_usages")
