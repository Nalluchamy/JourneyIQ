from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderRead
from app.schemas.response import APIResponse
from app.utils.event_logger import log_event
from app.utils.pagination import paginate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[OrderRead], summary="Get list of customer orders")
async def get_orders(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    status: str | None = Query(None, description="Filter by order status"),
    total_min: Decimal | None = Query(None, ge=0, description="Filter: orders equal or greater than amount"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get paginated orders list. If user is a customer, automatically filters to their own orders."""
    query = select(Order).options(selectinload(Order.items), selectinload(Order.status_history))

    if current_user.role == "customer":
        query = query.where(Order.user_id == current_user.id)
    elif user_id is not None:
        query = query.where(Order.user_id == user_id)

    if status:
        query = query.where(Order.status == status)

    if total_min is not None:
        query = query.where(Order.total >= total_min)

    query = query.order_by(Order.id.desc())
    paginated_data = await paginate(db, query, page, size)
    return paginated_data


@router.get("/history", response_model=PaginatedResponse[OrderRead], summary="Get order history for current logged in user")
async def get_order_history(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status: str | None = Query(None, description="Filter by order status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve the current authenticated user's order history, ordered by creation date descending."""
    query = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(selectinload(Order.items), selectinload(Order.status_history))
    )

    if status:
        query = query.where(Order.status == status)

    query = query.order_by(Order.id.desc())
    paginated_data = await paginate(db, query, page, size)
    return paginated_data


@router.get("/{order_id}", response_model=OrderRead, summary="Get details for a specific order")
async def get_order_by_id(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve full order details including line items, address, and status transition logs."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.status_history),
            selectinload(Order.shipping_address)
        )
    )
    order = (await db.execute(stmt)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )

    # Scoping check: customers can only access their own orders
    if current_user.role == "customer" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this order."
        )

    return order


@router.patch("/{order_id}/cancel", response_model=APIResponse[OrderRead], summary="Cancel an order and restore stock")
async def cancel_order(
    request: Request,
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Cancel a pending or confirmed order, releasing reserved product quantities back into inventory."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.status_history),
            selectinload(Order.user)
        )
    )
    order = (await db.execute(stmt)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )

    # Scoping check
    if current_user.role == "customer" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to cancel this order."
        )

    # State validation
    if order.status not in ["pending", "confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order in '{order.status}' status. Only Pending or Confirmed orders can be cancelled."
        )

    try:
        # 1. Update Order status
        order.status = "cancelled"

        # 2. Restore stock for each item
        for item in order.items:
            if item.product:
                item.product.stock += item.quantity

        # 3. Log status history log
        history = OrderStatusHistory(
            order_id=order.id,
            status="cancelled",
            notes=f"Order cancelled by {'customer' if current_user.role == 'customer' else 'staff'}.",
        )
        db.add(history)
        order.status_history.append(history)

        # 4. Log event
        await log_event(
            db,
            request,
            "order_cancelled",
            user_id=order.user_id,
            metadata={"order_id": order.id, "invoice_number": order.invoice_number},
        )

        # Send mock email
        print(f"\n--- [MOCK MAIL SENDER] ---\nTo: {order.user.email}\nSubject: Order Cancelled {order.invoice_number}\nStatus: CANCELLED\n---------------------------\n")

        await db.commit()

        # Re-fetch fresh order with selectinload to avoid lazy-loading serialization failures
        fresh_stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.status_history),
                selectinload(Order.shipping_address)
            )
        )
        fresh_order = (await db.execute(fresh_stmt)).scalar_one()

        return APIResponse(
            success=True,
            message="Order cancelled successfully. Stock levels restored.",
            data=fresh_order
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not cancel order: {e!s}"
        )


@router.get("/{order_id}/invoice", summary="Download invoice JSON data")
async def get_order_invoice(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve detailed order information structured as a printable invoice payload."""
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.shipping_address)
        )
    )
    order = (await db.execute(stmt)).scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )

    # Scoping check
    if current_user.role == "customer" and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view invoice for this order."
        )

    # Build Invoice JSON representation
    items_list = []
    for item in order.items:
        items_list.append({
            "product_name": item.product.name if item.product else "Unknown Product",
            "brand": item.product.brand if item.product else "",
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "subtotal": float(item.subtotal),
        })

    address_info = {}
    if order.shipping_address:
        addr = order.shipping_address
        address_info = {
            "full_name": addr.full_name,
            "phone": addr.phone,
            "address_line1": addr.address_line1,
            "address_line2": addr.address_line2,
            "city": addr.city,
            "state": addr.state,
            "country": addr.country,
            "postal_code": addr.postal_code,
        }

    return {
        "invoice_number": order.invoice_number,
        "issue_date": order.created_at.isoformat() if order.created_at else None,
        "payment_status": "Paid" if order.status not in ["pending", "cancelled"] else "Unpaid",
        "order_status": order.status,
        "billing_address": address_info,
        "shipping_address": address_info,
        "items": items_list,
        "summary": {
            "subtotal": float(order.subtotal),
            "tax": float(order.tax),
            "discount": float(order.discount),
            "shipping": 10.0 if order.subtotal > 0 else 0.0,
            "total": float(order.total),
        }
    }
