from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.order import Order
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderRead
from app.utils.pagination import paginate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[OrderRead],
    summary="Get paginated list of customer orders",
)
async def get_orders(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    status: str | None = Query(None, description="Filter by order status"),
    total_min: Decimal | None = Query(
        None, ge=0, description="Filter: orders equal or greater than amount"
    ),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Use selectinload to prevent N+1 query issues when loading order items
    query = select(Order).options(selectinload(Order.items))

    if user_id is not None:
        query = query.where(Order.user_id == user_id)

    if status:
        query = query.where(Order.status == status)

    if total_min is not None:
        query = query.where(Order.total >= total_min)

    # Order by ID descending (newest first)
    query = query.order_by(Order.id.desc())

    paginated_data = await paginate(db, query, page, size)
    return paginated_data
