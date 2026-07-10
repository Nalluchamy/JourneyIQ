from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    db: AsyncSession,
    query: Any,  # SQLAlchemy select statement
    page: int = 1,
    size: int = 20,
) -> dict[str, Any]:
    """Execute standard paginated search queries on database.

    Args:
        db (AsyncSession): Active SQLAlchemy session.
        query (Any): Select statement query.
        page (int): Current page (1-indexed).
        size (int): Records per page.

    Returns:
        dict[str, Any]: Pagination dict envelope matching PaginatedResponse schema keys.
    """
    if page < 1:
        page = 1
    if size < 1:
        size = 20

    offset = (page - 1) * size

    # Get total count using a count query wrapping a subquery of the main search
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Fetch rows
    items_query = query.limit(size).offset(offset)
    items_result = await db.execute(items_query)
    items = items_result.scalars().all()

    # Calculate total pages
    pages = (total + size - 1) // size if size > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }
