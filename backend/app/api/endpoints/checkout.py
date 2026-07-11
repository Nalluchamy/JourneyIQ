import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.cart_item import CartItem
from app.models.coupon import Coupon
from app.models.coupon_usage import CouponUsage
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.payment import Payment
from app.models.shipping_address import ShippingAddress
from app.models.user import User
from app.schemas.coupon import CouponApplyRequest, CouponApplyResponse
from app.schemas.order import CartSummaryResponse, CheckoutRequest, CheckoutResponse
from app.utils.event_logger import log_event

router = APIRouter()


async def calculate_totals(
    db: AsyncSession,
    user_id: int,
    coupon_code: str | None = None,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Coupon | None]:
    """Helper to calculate order subtotal, tax, shipping, discount, and grand total."""
    # Retrieve cart items
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
    )
    result = await db.execute(stmt)
    cart_items = result.scalars().all()

    subtotal = Decimal("0.00")
    for item in cart_items:
        if not item.product or item.product.is_deleted:
            continue
        subtotal += Decimal(str(item.product.price)) * item.quantity

    # Tax: 8%
    tax = (subtotal * Decimal("0.08")).quantize(Decimal("0.01"))

    # Shipping: flat $10.00
    shipping = Decimal("10.00") if subtotal > 0 else Decimal("0.00")

    discount = Decimal("0.00")
    coupon_obj: Coupon | None = None

    if coupon_code and subtotal > 0:
        # Validate coupon
        now = datetime.datetime.now(datetime.UTC)
        coupon_stmt = select(Coupon).where(
            Coupon.code == coupon_code.strip().upper(),
            Coupon.is_active == True,
            Coupon.start_date <= now,
            Coupon.expiry_date >= now,
        )
        coupon_obj = (await db.execute(coupon_stmt)).scalar_one_or_none()

        if coupon_obj:
            # Check minimum order
            if subtotal >= coupon_obj.minimum_order:
                # Check usage limits
                if coupon_obj.usage_limit > 0:
                    usage_stmt = select(func.count(CouponUsage.id)).where(
                        CouponUsage.coupon_id == coupon_obj.id
                    )
                    usages_count = (await db.execute(usage_stmt)).scalar() or 0
                    if usages_count >= coupon_obj.usage_limit:
                        coupon_obj = None  # limit reached

                if coupon_obj:
                    # Apply discount
                    if coupon_obj.discount_type == "percentage":
                        raw_discount = subtotal * (coupon_obj.discount_value / Decimal("100.00"))
                        if coupon_obj.maximum_discount:
                            discount = min(raw_discount, coupon_obj.maximum_discount)
                        else:
                            discount = raw_discount
                    elif coupon_obj.discount_type == "fixed":
                        discount = min(coupon_obj.discount_value, subtotal)

                    discount = discount.quantize(Decimal("0.01"))

    grand_total = max(Decimal("0.00"), subtotal + tax + shipping - discount)
    return subtotal, tax, shipping, discount, grand_total, coupon_obj


@router.get("/cart/summary", response_model=CartSummaryResponse, summary="Retrieve current cart summary with price calculations")
async def get_cart_summary(
    coupon_code: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Calculate and return subtotal, tax, shipping, discount, and grand total for user's cart."""
    subtotal, tax, shipping, discount, grand_total, _ = await calculate_totals(
        db, current_user.id, coupon_code
    )
    return {
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "discount": discount,
        "grand_total": grand_total,
    }


@router.post("/checkout/apply-coupon", response_model=CouponApplyResponse, summary="Validate and apply coupon code to cart")
async def apply_coupon(
    payload: CouponApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Validate a coupon code and calculate the discount amount for a given cart total."""
    now = datetime.datetime.now(datetime.UTC)
    coupon_stmt = select(Coupon).where(
        Coupon.code == payload.code.strip().upper(),
        Coupon.is_active == True,
        Coupon.start_date <= now,
        Coupon.expiry_date >= now,
    )
    coupon = (await db.execute(coupon_stmt)).scalar_one_or_none()

    if not coupon:
        return {
            "code": payload.code,
            "discount_type": "percentage",
            "discount_value": Decimal("0.00"),
            "discount_amount": Decimal("0.00"),
            "is_valid": False,
            "message": "Invalid or expired coupon code.",
        }

    if payload.cart_total < coupon.minimum_order:
        return {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": coupon.discount_value,
            "discount_amount": Decimal("0.00"),
            "is_valid": False,
            "message": f"Coupon requires a minimum order of ${coupon.minimum_order:.2f}.",
        }

    # Check usage limit
    if coupon.usage_limit > 0:
        usage_stmt = select(func.count(CouponUsage.id)).where(
            CouponUsage.coupon_id == coupon.id
        )
        usages_count = (await db.execute(usage_stmt)).scalar() or 0
        if usages_count >= coupon.usage_limit:
            return {
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "discount_amount": Decimal("0.00"),
                "is_valid": False,
                "message": "Coupon usage limit has been reached.",
            }

    # Calculate discount
    discount = Decimal("0.00")
    if coupon.discount_type == "percentage":
        raw_discount = payload.cart_total * (coupon.discount_value / Decimal("100.00"))
        if coupon.maximum_discount:
            discount = min(raw_discount, coupon.maximum_discount)
        else:
            discount = raw_discount
    elif coupon.discount_type == "fixed":
        discount = min(coupon.discount_value, payload.cart_total)

    discount_amount = discount.quantize(Decimal("0.01"))
    return {
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount_amount,
        "is_valid": True,
        "message": f"Coupon '{coupon.code}' applied successfully!",
    }


async def generate_invoice_number(db: AsyncSession) -> str:
    """Helper to generate sequential unique invoice numbers (e.g. INV-2026-000001)."""
    year = datetime.datetime.now().year
    stmt = (
        select(Order.invoice_number)
        .where(Order.invoice_number.like(f"INV-{year}-%"))
        .order_by(Order.id.desc())
        .limit(1)
    )
    last_invoice = (await db.execute(stmt)).scalar_one_or_none()

    if last_invoice:
        try:
            seq_part = last_invoice.split("-")[-1]
            next_seq = int(seq_part) + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1

    return f"INV-{year}-{next_seq:06d}"


@router.post("/checkout", response_model=CheckoutResponse, summary="Perform atomic checkout transaction")
async def checkout(
    request: Request,
    payload: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Atomic checkout transaction validation, stock updates, event recording, and order creation."""
    # 1. Fetch and validate shipping address exists and belongs to current user
    addr_stmt = select(ShippingAddress).where(
        ShippingAddress.id == payload.shipping_address_id,
        ShippingAddress.user_id == current_user.id,
    )
    address = (await db.execute(addr_stmt)).scalar_one_or_none()
    if not address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid shipping address is required for checkout.",
        )

    # 2. Fetch cart items with product info
    cart_stmt = (
        select(CartItem)
        .where(CartItem.user_id == current_user.id)
        .options(selectinload(CartItem.product))
    )
    cart_items = (await db.execute(cart_stmt)).scalars().all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your shopping cart is empty.",
        )

    # Prevent duplicate submit/checkout: Check if a similar order exists from the user in the last 3 seconds
    recent_order_stmt = select(Order).where(
        Order.user_id == current_user.id,
        Order.created_at >= datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=3),
    )
    recent_order = (await db.execute(recent_order_stmt)).scalar_one_or_none()
    if recent_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate checkout request detected. Please wait a moment.",
        )

    # Begin single atomic SQLAlchemy Transaction block
    try:
        # Validate stock and active status of all items in cart
        for item in cart_items:
            product = item.product
            if not product or product.is_deleted or not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product.name if product else 'Unknown'}' is no longer active.",
                )
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product '{product.name}'. Only {product.stock} items left.",
                )

        # 3. Calculate totals and validate coupon
        subtotal, tax, shipping, discount, grand_total, coupon = await calculate_totals(
            db, current_user.id, payload.coupon_code
        )

        # 4. Generate Invoice number
        invoice_number = await generate_invoice_number(db)

        # 5. Create Order
        order = Order(
            user_id=current_user.id,
            status="pending",
            subtotal=subtotal,
            tax=tax,
            discount=discount,
            total=grand_total,
            invoice_number=invoice_number,
            shipping_address_id=address.id,
        )
        db.add(order)
        await db.flush()  # populate order.id

        # 6. Create OrderItems & deduct stock
        for item in cart_items:
            product = item.product
            # Deduct stock
            product.stock -= item.quantity

            # Create item
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price,
                subtotal=Decimal(str(product.price)) * item.quantity,
            )
            db.add(order_item)

        # 7. Create Payment record (pending status)
        payment = Payment(
            order_id=order.id,
            payment_provider="mock",
            payment_id=None,
            status="pending",
            amount=grand_total,
            currency="USD",
        )
        db.add(payment)

        # 8. Create OrderStatusHistory (Pending status)
        history = OrderStatusHistory(
            order_id=order.id,
            status="pending",
            notes="Order placed. Awaiting payment authorization.",
        )
        db.add(history)

        # 9. Record coupon usage if valid coupon applied
        if coupon:
            coupon_usage = CouponUsage(
                coupon_id=coupon.id,
                user_id=current_user.id,
                order_id=order.id,
            )
            db.add(coupon_usage)
            # Log coupon_applied event
            await log_event(db, request, "coupon_applied", user_id=current_user.id, metadata={"coupon_code": coupon.code})

        # 10. Clear cart items
        for item in cart_items:
            await db.delete(item)

        # 11. Log checkout events
        await log_event(db, request, "checkout_started", user_id=current_user.id)
        await log_event(db, request, "checkout_completed", user_id=current_user.id, metadata={"order_id": order.id, "invoice_number": invoice_number})

        # Log confirmation to mock email log
        print(f"\n--- [MOCK MAIL SENDER] ---\nTo: {current_user.email}\nSubject: Order Confirmation {invoice_number}\nStatus: PENDING\nTotal: ${grand_total:.2f}\n---------------------------\n")

        await db.commit()
        return {
            "order_id": order.id,
            "invoice_number": invoice_number,
            "payment_status": "pending",
        }

    except Exception as e:
        await db.rollback()
        # Reraise HTTP exceptions as is, or raise generic 400 for transactions
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Checkout transaction failed: {e!s}",
        )
