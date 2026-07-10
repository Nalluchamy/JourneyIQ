from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter()


@router.get("/products/{product_id}/reviews", response_model=APIResponse[list[ReviewRead]])
async def get_product_reviews(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Retrieve public reviews for a product, sorted newest first."""
    stmt = (
        select(Review)
        .where(Review.product_id == product_id)
        .options(selectinload(Review.user))
        .order_by(Review.id.desc())
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    return APIResponse(
        success=True, message="Reviews retrieved successfully.", data=reviews
    )


@router.post(
    "/products/{product_id}/reviews",
    response_model=APIResponse[ReviewRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_product_review(
    product_id: int,
    body: ReviewCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Create a new product review, verifying the user has purchased the item."""
    # Check if product exists
    prod_stmt = select(Product).where(
        Product.id == product_id, Product.is_deleted == False
    )
    product = (await db.execute(prod_stmt)).scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    # Verification: Only users who purchased this product in a completed/shipped order can review it
    purchase_stmt = (
        select(OrderItem)
        .join(Order)
        .where(
            Order.user_id == current_user.id,
            Order.status.in_(["completed", "shipped"]),
            OrderItem.product_id == product_id,
        )
    )
    purchase = (await db.execute(purchase_stmt)).scalar_one_or_none()
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only verified purchasers who completed an order for this product can leave reviews.",
        )

    # Check if user already reviewed this product
    existing_stmt = select(Review).where(
        Review.user_id == current_user.id, Review.product_id == product_id
    )
    existing_review = (await db.execute(existing_stmt)).scalar_one_or_none()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product. Please edit your existing review instead.",
        )

    # Create review
    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        rating=body.rating,
        review=body.review,
    )
    db.add(review)
    await db.flush()  # Populate review.id

    await db.commit()

    # Load with user details
    stmt = (
        select(Review)
        .where(Review.id == review.id)
        .options(selectinload(Review.user))
    )
    loaded_review = (await db.execute(stmt)).scalar_one()

    return APIResponse(
        success=True, message="Review submitted successfully.", data=loaded_review
    )


@router.patch("/reviews/{review_id}", response_model=APIResponse[ReviewRead])
async def update_review(
    review_id: int,
    body: ReviewUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Modify an existing product review (restricted to review owner or admin)."""
    stmt = select(Review).where(Review.id == review_id)
    review = (await db.execute(stmt)).scalar_one_or_none()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found."
        )

    # Security check: owner or admin
    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only edit your own reviews.",
        )

    # Apply updates
    if body.rating is not None:
        review.rating = body.rating
    if body.review is not None:
        review.review = body.review

    await db.commit()

    # Reload with user details
    stmt = (
        select(Review)
        .where(Review.id == review.id)
        .options(selectinload(Review.user))
    )
    loaded_review = (await db.execute(stmt)).scalar_one()

    return APIResponse(
        success=True, message="Review updated successfully.", data=loaded_review
    )


@router.delete("/reviews/{review_id}", response_model=APIResponse[None])
async def delete_review(
    review_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Delete a product review (restricted to review owner or admin)."""
    stmt = select(Review).where(Review.id == review_id)
    review = (await db.execute(stmt)).scalar_one_or_none()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found."
        )

    # Security check: owner or admin
    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only delete your own reviews.",
        )

    await db.delete(review)
    await db.commit()

    return APIResponse(success=True, message="Review deleted successfully.", data=None)
