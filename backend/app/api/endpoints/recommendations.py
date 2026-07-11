from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.recommendation import Recommendation
from app.models.product import Product
from app.models.review import Review
from app.models.order_item import OrderItem
from app.models.event import Event
from app.models.user import User
from app.schemas.recommendation import RecommendationRead
from app.schemas.product import ProductRead
from app.schemas.response import APIResponse

router = APIRouter()


@router.get("", response_model=APIResponse[list[RecommendationRead]], summary="Get personalized product recommendations")
async def get_personalized_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve personalized recommendations for the authenticated customer. Fallback to trending if empty."""
    stmt = (
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .options(selectinload(Recommendation.product))
        .order_by(Recommendation.score.desc())
        .limit(10)
    )
    res = await db.execute(stmt)
    recs = res.scalars().all()

    # Fallback to trending products if no recommendations are pre-generated (e.g. cold-start)
    if not recs:
        # Query top 10 trending items from Events
        trend_stmt = (
            select(Event.product_id, func.count(Event.id).label("views"))
            .where(Event.event_type == "view_item", Event.product_id.isnot(None))
            .group_by(Event.product_id)
            .order_by(func.count(Event.id).desc())
            .limit(10)
        )
        trend_res = await db.execute(trend_stmt)
        trending_pids = [row[0] for row in trend_res.all()]

        if not trending_pids:
            # Absolute fallback: standard top products
            prod_stmt = select(Product).where(Product.is_deleted == False, Product.is_active == True).limit(10)
            prods = (await db.execute(prod_stmt)).scalars().all()
        else:
            prod_stmt = select(Product).where(Product.id.in_(trending_pids), Product.is_deleted == False, Product.is_active == True)
            prods = (await db.execute(prod_stmt)).scalars().all()

        recs = [
            Recommendation(
                user_id=current_user.id,
                product_id=p.id,
                score=1.0,
                explanation="Trending this week.",
                product=p
            )
            for p in prods
        ]

    # Map generated_at timezone attributes if needed
    return APIResponse(
        success=True,
        message="Recommendations retrieved successfully.",
        data=recs
    )


@router.get("/trending", response_model=APIResponse[list[ProductRead]], summary="Get trending products list")
async def get_trending_products(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve trending products list based on recent view events."""
    trend_stmt = (
        select(Product, func.count(Event.id).label("views"))
        .join(Event, Event.product_id == Product.id)
        .where(Event.event_type == "view_item", Product.is_deleted == False, Product.is_active == True)
        .group_by(Product.id)
        .order_by(func.count(Event.id).desc())
        .limit(10)
    )
    res = await db.execute(trend_stmt)
    products = [row[0] for row in res.all()]

    # Fallback to basic products list if no event views exist yet
    if not products:
        fallback_stmt = select(Product).where(Product.is_deleted == False, Product.is_active == True).limit(10)
        products = (await db.execute(fallback_stmt)).scalars().all()

    return APIResponse(
        success=True,
        message="Trending products retrieved successfully.",
        data=products
    )


@router.get("/popular", response_model=APIResponse[list[ProductRead]], summary="Get popular products list")
async def get_popular_products(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve popular products based on customer purchase items count and top ratings."""
    pop_stmt = (
        select(Product, func.sum(OrderItem.quantity).label("sales"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .where(Product.is_deleted == False, Product.is_active == True)
        .group_by(Product.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
    )
    res = await db.execute(pop_stmt)
    products = [row[0] for row in res.all()]

    # Fallback to average ratings if no orders have been placed
    if not products:
        ratings_stmt = (
            select(Product, func.avg(Review.rating).label("avg_rating"))
            .join(Review, Review.product_id == Product.id)
            .where(Product.is_deleted == False, Product.is_active == True)
            .group_by(Product.id)
            .order_by(func.avg(Review.rating).desc())
            .limit(10)
        )
        ratings_res = await db.execute(ratings_stmt)
        products = [row[0] for row in ratings_res.all()]

    # General fallback
    if not products:
        fallback_stmt = select(Product).where(Product.is_deleted == False, Product.is_active == True).limit(10)
        products = (await db.execute(fallback_stmt)).scalars().all()

    return APIResponse(
        success=True,
        message="Popular products retrieved successfully.",
        data=products
    )
