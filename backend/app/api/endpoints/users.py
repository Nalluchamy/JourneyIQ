from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserRead
from app.utils.pagination import paginate

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    summary="Get paginated list of active users",
)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Search by name or email"),
    role: str | None = Query(None, description="Filter by role (e.g. customer, admin)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    # Filter out soft-deleted users
    query = select(User).where(User.is_deleted == False)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            or_(
                User.full_name.ilike(search_filter),
                User.email.ilike(search_filter),
            )
        )

    if role:
        query = query.where(User.role == role)

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # Order by ID ascending
    query = query.order_by(User.id.asc())

    paginated_data = await paginate(db, query, page, size)
    return paginated_data
