from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.models.wishlist_item import WishlistItem
from app.schemas.response import APIResponse
from app.schemas.wishlist import WishlistItemCreate, WishlistItemRead
from app.utils.event_logger import log_event

router = APIRouter()


@router.get("", response_model=APIResponse[list[WishlistItemRead]])
async def get_wishlist(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Retrieve all wishlist items for the authenticated user."""
    stmt = (
        select(WishlistItem)
        .where(WishlistItem.user_id == current_user.id)
        .options(selectinload(WishlistItem.product))
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return APIResponse(
        success=True, message="Wishlist retrieved successfully.", data=items
    )


@router.post("", response_model=APIResponse[WishlistItemRead], status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    request: Request,
    body: WishlistItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Add a product to the user's wishlist, avoiding duplicates."""
    # Check if product exists and is active
    prod_stmt = select(Product).where(
        Product.id == body.product_id, Product.is_deleted == False
    )
    product = (await db.execute(prod_stmt)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    # Check for existing wishlist item
    dup_stmt = select(WishlistItem).where(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == body.product_id,
    )
    duplicate = (await db.execute(dup_stmt)).scalar_one_or_none()
    if duplicate:
        stmt = (
            select(WishlistItem)
            .where(WishlistItem.id == duplicate.id)
            .options(selectinload(WishlistItem.product))
        )
        existing_item = (await db.execute(stmt)).scalar_one()
        return APIResponse(
            success=True,
            message="Product is already in your wishlist.",
            data=existing_item,
        )

    # Insert new wishlist entry
    item = WishlistItem(user_id=current_user.id, product_id=body.product_id)
    db.add(item)
    await db.flush()  # Populate item.id

    # Track wishlist add event
    await log_event(
        db,
        request,
        "wishlist_add",
        user_id=current_user.id,
        product_id=body.product_id,
    )
    await db.commit()

    # Load with product details
    stmt = (
        select(WishlistItem)
        .where(WishlistItem.id == item.id)
        .options(selectinload(WishlistItem.product))
    )
    loaded_item = (await db.execute(stmt)).scalar_one()

    return APIResponse(
        success=True, message="Product added to wishlist.", data=loaded_item
    )


@router.delete("/{product_id}", response_model=APIResponse[None])
async def remove_from_wishlist(
    request: Request,
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Remove a product from the user's wishlist."""
    stmt = select(WishlistItem).where(
        WishlistItem.user_id == current_user.id,
        WishlistItem.product_id == product_id,
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not in your wishlist.",
        )

    await db.delete(item)

    # Track wishlist remove event
    await log_event(
        db,
        request,
        "wishlist_remove",
        user_id=current_user.id,
        product_id=product_id,
    )
    await db.commit()

    return APIResponse(
        success=True, message="Product removed from wishlist.", data=None
    )
