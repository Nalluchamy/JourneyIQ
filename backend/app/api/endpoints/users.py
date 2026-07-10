from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserRead, UserUpdate
from app.utils.pagination import paginate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    summary="Retrieve details of currently logged-in user",
)
async def get_my_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> Any:
    """Get profile information for the authenticated user."""
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update details of currently logged-in user",
)
async def update_my_profile(
    body: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Update profile information (name, phone) for the authenticated user."""
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.phone is not None:
        current_user.phone = body.phone

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get(
    "",
    response_model=PaginatedResponse[UserRead],
    summary="Get paginated list of active users",
)
async def get_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Search by name or email"),
    role: str | None = Query(None, description="Filter by role (e.g. customer, admin)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
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
