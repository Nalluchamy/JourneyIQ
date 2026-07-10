import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import BaseModel

if TYPE_CHECKING:
    from app.models.coupon_usage import CouponUsage


class Coupon(BaseModel):
    """Coupon DB Model."""

    __tablename__ = "coupon"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "percentage" or "fixed"
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    minimum_order: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), server_default="0.00", nullable=False)
    maximum_discount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    start_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usage_limit: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)  # 0 means unlimited
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    # Relationships
    usages: Mapped[list["CouponUsage"]] = relationship(back_populates="coupon", cascade="all, delete-orphan")
