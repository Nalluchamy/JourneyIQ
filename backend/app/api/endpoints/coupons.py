import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.coupon import Coupon
from app.schemas.coupon import CouponRead

router = APIRouter()


async def ensure_demo_coupons(db: AsyncSession) -> None:
    """Helper to auto-seed standard demo coupons if the database is currently empty."""
    result = await db.execute(select(Coupon).limit(1))
    if result.scalar_one_or_none() is not None:
        return  # Already seeded

    now = datetime.datetime.now(datetime.timezone.utc)
    expiry = now + datetime.timedelta(days=365)

    demo_coupons = [
        Coupon(
            code="WELCOME10",
            description="Get 10% off on your first order over $50",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            minimum_order=Decimal("50.00"),
            maximum_discount=Decimal("20.00"),
            start_date=now,
            expiry_date=expiry,
            usage_limit=0,
            is_active=True,
        ),
        Coupon(
            code="WELCOME20",
            description="Get 20% off on your order over $100",
            discount_type="percentage",
            discount_value=Decimal("20.00"),
            minimum_order=Decimal("100.00"),
            maximum_discount=Decimal("50.00"),
            start_date=now,
            expiry_date=expiry,
            usage_limit=0,
            is_active=True,
        ),
        Coupon(
            code="SUMMER25",
            description="Summer special: 25% off on orders over $120",
            discount_type="percentage",
            discount_value=Decimal("25.00"),
            minimum_order=Decimal("120.00"),
            maximum_discount=Decimal("75.00"),
            start_date=now,
            expiry_date=expiry,
            usage_limit=0,
            is_active=True,
        ),
        Coupon(
            code="FESTIVAL15",
            description="Festival sale: 15% off on orders over $80",
            discount_type="percentage",
            discount_value=Decimal("15.00"),
            minimum_order=Decimal("80.00"),
            maximum_discount=Decimal("40.00"),
            start_date=now,
            expiry_date=expiry,
            usage_limit=0,
            is_active=True,
        ),
        Coupon(
            code="FREESHIP",
            description="Get free shipping (flat $10 off) on orders over $40",
            discount_type="fixed",
            discount_value=Decimal("10.00"),
            minimum_order=Decimal("40.00"),
            maximum_discount=Decimal("10.00"),
            start_date=now,
            expiry_date=expiry,
            usage_limit=0,
            is_active=True,
        ),
    ]

    db.add_all(demo_coupons)
    await db.commit()


@router.get("", response_model=list[CouponRead], summary="Get list of all active coupons")
async def get_active_coupons(db: AsyncSession = Depends(get_db)) -> Any:
    """Retrieve all active, non-expired coupons. Seeds demo coupons first if none exist."""
    await ensure_demo_coupons(db)
    now = datetime.datetime.now(datetime.timezone.utc)
    result = await db.execute(
        select(Coupon).where(
            Coupon.is_active == True,
            Coupon.start_date <= now,
            Coupon.expiry_date >= now,
        )
    )
    return result.scalars().all()
