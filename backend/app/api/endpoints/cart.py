from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemRead, CartItemUpdate
from app.schemas.response import APIResponse
from app.utils.event_logger import log_event

router = APIRouter()


@router.get("", response_model=APIResponse[list[CartItemRead]])
async def get_cart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Retrieve all shopping cart items for the authenticated user."""
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == current_user.id)
        .options(selectinload(CartItem.product))
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return APIResponse(
        success=True, message="Cart retrieved successfully.", data=items
    )


@router.post("", response_model=APIResponse[CartItemRead], status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    request: Request,
    body: CartItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Add a product or increment quantity in the user's cart, validating stock availability."""
    # Check if product exists and is active
    prod_stmt = select(Product).where(
        Product.id == body.product_id, Product.is_deleted == False
    )
    product = (await db.execute(prod_stmt)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    # Check stock
    if product.stock < body.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Only {product.stock} items available.",
        )

    # Check for existing cart item
    dup_stmt = select(CartItem).where(
        CartItem.user_id == current_user.id,
        CartItem.product_id == body.product_id,
    )
    existing_item = (await db.execute(dup_stmt)).scalar_one_or_none()

    if existing_item:
        new_qty = existing_item.quantity + body.quantity
        if product.stock < new_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add {body.quantity} more items. Cart quantity ({new_qty}) exceeds stock ({product.stock}).",
            )
        existing_item.quantity = new_qty
        item_id = existing_item.id
    else:
        # Create new cart entry
        item = CartItem(
            user_id=current_user.id,
            product_id=body.product_id,
            quantity=body.quantity,
        )
        db.add(item)
        await db.flush()  # Populate item.id
        item_id = item.id

    # Track cart add event
    await log_event(
        db,
        request,
        "cart_add",
        user_id=current_user.id,
        product_id=body.product_id,
        metadata={"quantity": body.quantity},
    )
    await db.commit()

    # Load with product details
    stmt = (
        select(CartItem)
        .where(CartItem.id == item_id)
        .options(selectinload(CartItem.product))
    )
    loaded_item = (await db.execute(stmt)).scalar_one()

    return APIResponse(
        success=True, message="Product added to cart.", data=loaded_item
    )


@router.put("/{product_id}", response_model=APIResponse[CartItemRead])
async def update_cart_quantity(
    product_id: int,
    body: CartItemUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Set the quantity for a product in the user's cart, validating stock availability."""
    # Check if product exists
    prod_stmt = select(Product).where(
        Product.id == product_id, Product.is_deleted == False
    )
    product = (await db.execute(prod_stmt)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    # Check stock
    if product.stock < body.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Only {product.stock} items available.",
        )

    # Find the cart item
    stmt = select(CartItem).where(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id,
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not in your cart.",
        )

    item.quantity = body.quantity
    await db.commit()

    # Reload with product details
    stmt = (
        select(CartItem)
        .where(CartItem.id == item.id)
        .options(selectinload(CartItem.product))
    )
    loaded_item = (await db.execute(stmt)).scalar_one()

    return APIResponse(
        success=True, message="Cart quantity updated.", data=loaded_item
    )


@router.delete("/{product_id}", response_model=APIResponse[None])
async def remove_from_cart(
    request: Request,
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Remove a product from the user's cart."""
    stmt = select(CartItem).where(
        CartItem.user_id == current_user.id,
        CartItem.product_id == product_id,
    )
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not in your cart.",
        )

    await db.delete(item)

    # Track cart remove event
    await log_event(
        db,
        request,
        "cart_remove",
        user_id=current_user.id,
        product_id=product_id,
    )
    await db.commit()

    return APIResponse(
        success=True, message="Product removed from cart.", data=None
    )


@router.delete("", response_model=APIResponse[None])
async def clear_cart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Clear all items from the user's cart."""
    stmt = select(CartItem).where(CartItem.user_id == current_user.id)
    items = (await db.execute(stmt)).scalars().all()

    for item in items:
        await db.delete(item)

    await db.commit()
    return APIResponse(success=True, message="Cart cleared successfully.", data=None)
