import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_optional, get_db
from app.models.event import Event
from app.models.product import Product
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.event import EventCreate, EventRead
from app.schemas.response import APIResponse
from app.utils.event_logger import log_event
from app.utils.pagination import paginate

router = APIRouter()


@router.post("", response_model=APIResponse[EventRead], status_code=status.HTTP_201_CREATED)
async def create_event(
    request: Request,
    body: EventCreate,
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Create a tracking event log (supports both guest and authenticated sessions)."""
    user_id = current_user.id if current_user else None

    # Resolve product existence if product_id is sent
    if body.product_id is not None:
        prod_stmt = select(Product).where(
            Product.id == body.product_id, Product.is_deleted == False
        )
        product = (await db.execute(prod_stmt)).scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
            )

    # Use general logging helper
    await log_event(
        db,
        request,
        event_type=body.event_type,
        user_id=user_id,
        product_id=body.product_id,
        metadata=body.metadata,
    )
    await db.commit()

    # Query last inserted event to return it loaded with timestamps
    session_str = request.headers.get("x-session-id")
    try:
        session_id = uuid.UUID(session_str) if session_str else uuid.uuid4()
    except (ValueError, TypeError):
        session_id = uuid.uuid4()

    latest_stmt = (
        select(Event)
        .where(Event.session_id == session_id, Event.event_type == body.event_type)
        .order_by(Event.id.desc())
        .limit(1)
    )
    latest_event = (await db.execute(latest_stmt)).scalar_one()

    return APIResponse(
        success=True, message="Event tracked successfully.", data=latest_event
    )


@router.get("/recent-views", response_model=APIResponse[list[EventRead]])
async def get_recent_views(
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
    session_id: uuid.UUID | None = Query(None, description="Fallback session UUID"),
) -> Any:
    """Retrieve the last 10 unique product views, excluding soft-deleted items."""
    query = (
        select(Event)
        .join(Product, Event.product_id == Product.id)
        .where(Product.is_deleted == False, Event.event_type == "product_view")
    )

    if current_user:
        query = query.where(Event.user_id == current_user.id)
    elif session_id:
        query = query.where(Event.session_id == session_id)
    else:
        return APIResponse(success=True, message="No recent views found.", data=[])

    # Query more than 10 to allow in-memory deduplication of products viewed repeatedly
    query = (
        query.order_by(Event.timestamp.desc())
        .limit(30)
        .options(selectinload(Event.product))
    )
    result = await db.execute(query)
    events = result.scalars().all()

    # Deduplicate in-memory by unique product_id while maintaining chronological order
    seen_products = set()
    unique_views = []
    for event in events:
        if event.product_id not in seen_products:
            seen_products.add(event.product_id)
            unique_views.append(event)
            if len(unique_views) >= 10:
                break

    return APIResponse(
        success=True, message="Recent views retrieved.", data=unique_views
    )


@router.get(
    "",
    response_model=PaginatedResponse[EventRead],
    summary="Get paginated list of tracking events",
)
async def get_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    session_id: uuid.UUID | None = Query(None, description="Filter by session UUID"),
    event_type: str | None = Query(
        None, description="Filter by event type (e.g. page_view, add_to_cart)"
    ),
) -> Any:
    query = select(Event)

    if user_id is not None:
        query = query.where(Event.user_id == user_id)

    if session_id is not None:
        query = query.where(Event.session_id == session_id)

    if event_type:
        query = query.where(Event.event_type == event_type)

    # Order by timestamp descending (newest first)
    query = query.order_by(Event.timestamp.desc())

    paginated_data = await paginate(db, query, page, size)
    return paginated_data
