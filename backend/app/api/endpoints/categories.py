from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.category import Category
from app.schemas.category import CategoryRead
from app.schemas.common import PaginatedResponse
from app.utils.pagination import paginate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[CategoryRead],
    summary="Get paginated list of categories",
)
async def get_categories(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Filter out soft-deleted categories
    query = select(Category).where(Category.is_deleted == False)

    if search:
        query = query.where(Category.name.ilike(f"%{search}%"))

    # Order by ID ascending
    query = query.order_by(Category.id.asc())

    paginated_data = await paginate(db, query, page, size)
    return paginated_data
