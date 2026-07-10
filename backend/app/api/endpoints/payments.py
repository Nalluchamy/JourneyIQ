from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.order import Order
from app.models.order_status_history import OrderStatusHistory
from app.models.payment import Payment
from app.schemas.response import APIResponse
from app.utils.event_logger import log_event

router = APIRouter()


@router.post("/mock-success/{order_id}", response_model=APIResponse[dict], summary="Mock a successful payment transaction")
async def mock_payment_success(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Mock payment success callback. Transitions Order to Confirmed and Payment to Success."""
    order_stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.payments), selectinload(Order.user))
    )
    order = (await db.execute(order_stmt)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    # Find the pending payment
    payment = next((p for p in order.payments if p.status == "pending"), None)
    if not payment:
        # If no pending payment, find the last payment
        if order.payments:
            payment = order.payments[-1]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No payment record found for this order.",
            )

    # Transition statuses
    payment.status = "success"
    payment.payment_id = f"mock_tx_success_{order.id}"
    order.status = "confirmed"

    # Add history log
    history = OrderStatusHistory(
        order_id=order.id,
        status="confirmed",
        notes="Mock payment succeeded. Order is now confirmed.",
    )
    db.add(history)

    # Log payment_success event
    await log_event(
        db,
        request,
        "payment_success",
        user_id=order.user_id,
        metadata={"order_id": order.id, "amount": float(payment.amount)},
    )

    # Log order_completed or payment_success email
    print(f"\n--- [MOCK MAIL SENDER] ---\nTo: {order.user.email}\nSubject: Payment Success for Order {order.invoice_number}\nStatus: SUCCESS\n---------------------------\n")

    await db.commit()
    return APIResponse(
        success=True,
        message="Payment processed successfully (Mock).",
        data={"order_id": order.id, "status": order.status, "invoice_number": order.invoice_number},
    )


@router.post("/mock-failure/{order_id}", response_model=APIResponse[dict], summary="Mock a failed payment transaction")
async def mock_payment_failure(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Mock payment failure callback. Transitions Payment to Failed; Order remains Pending."""
    order_stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.payments), selectinload(Order.user))
    )
    order = (await db.execute(order_stmt)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    # Find the pending payment
    payment = next((p for p in order.payments if p.status == "pending"), None)
    if not payment:
        if order.payments:
            payment = order.payments[-1]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No payment record found for this order.",
            )

    # Transition payment to failed (Order remains Pending)
    payment.status = "failed"
    payment.payment_id = f"mock_tx_failed_{order.id}"

    # Add history log
    history = OrderStatusHistory(
        order_id=order.id,
        status="pending",
        notes="Mock payment authorization failed. Retrying payment required.",
    )
    db.add(history)

    # Log payment_failed event
    await log_event(
        db,
        request,
        "payment_failed",
        user_id=order.user_id,
        metadata={"order_id": order.id, "amount": float(payment.amount)},
    )

    # Log payment_failed email
    print(f"\n--- [MOCK MAIL SENDER] ---\nTo: {order.user.email}\nSubject: Payment Failed for Order {order.invoice_number}\nStatus: FAILED\n---------------------------\n")

    await db.commit()
    return APIResponse(
        success=True,
        message="Payment authorization failed (Mock).",
        data={"order_id": order.id, "status": order.status, "invoice_number": order.invoice_number},
    )
