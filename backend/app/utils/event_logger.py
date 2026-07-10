import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


async def log_event(
    db: AsyncSession,
    request: Request,
    event_type: str,
    user_id: int | None = None,
    product_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Extract session from request headers and write an Event record to the database."""
    session_str = request.headers.get("x-session-id")
    try:
        session_id = uuid.UUID(session_str) if session_str else uuid.uuid4()
    except (ValueError, TypeError):
        session_id = uuid.uuid4()

    event = Event(
        user_id=user_id,
        session_id=session_id,
        event_type=event_type,
        page=request.url.path,
        product_id=product_id,
        metadata_=metadata,
    )
    db.add(event)
