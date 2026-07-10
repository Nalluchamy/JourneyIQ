import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.event import Event
from app.schemas.common import PaginatedResponse
from app.schemas.event import EventRead
from app.utils.pagination import paginate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[EventRead],
    summary="Get paginated list of tracking events",
)
async def get_events(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    session_id: uuid.UUID | None = Query(None, description="Filter by session UUID"),
    event_type: str | None = Query(
        None, description="Filter by event type (e.g. page_view, add_to_cart)"
    ),
    db: AsyncSession = Depends(get_db),
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
