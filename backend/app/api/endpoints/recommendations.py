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


# ========================================================
# DEEP LEARNING RECOMMENDATION ENGINE ENDPOINTS (NCF)
# ========================================================
import os
import json
from app.services.deep_learning.inference import NCFInferenceService

MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models"))


@router.get("/deep", summary="Get deep learning product recommendations")
async def get_deep_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve personalized product recommendations generated by the PyTorch NCF model."""
    service = NCFInferenceService()
    recs = await service.recommend_for_user(current_user.id, db)
    return APIResponse(
        success=True,
        message="Deep learning recommendations retrieved successfully.",
        data=recs
    )


@router.get("/deep/similar/{product_id}", summary="Get deep learning similar products")
async def get_deep_similar_products(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve similar products computed from PyTorch item embedding cosine similarities."""
    service = NCFInferenceService()
    similar = await service.similar_products(product_id, db)
    return APIResponse(
        success=True,
        message="Deep learning similar products retrieved successfully.",
        data=similar
    )


@router.get("/deep/compare", summary="Compare hybrid vs deep learning models")
async def compare_recommendation_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve recommendation scores, metrics, training latency, and model metadata side-by-side."""
    # 1. Fetch Hybrid Recommendations
    hybrid_stmt = (
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .options(selectinload(Recommendation.product))
        .limit(10)
    )
    hybrid_res = await db.execute(hybrid_stmt)
    hybrid_recs = hybrid_res.scalars().all()

    # 2. Fetch Deep Learning Recommendations
    service = NCFInferenceService()
    deep_recs = await service.recommend_for_user(current_user.id, db, limit=10)

    # 3. Read metadata and metrics
    metadata = {}
    metrics = {}
    
    metadata_path = os.path.join(MODEL_DIR, "model_metadata.json")
    metrics_path = os.path.join(MODEL_DIR, "evaluation_metrics.json")
    
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        except Exception:
            pass
            
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
        except Exception:
            pass

    comparison = {
        "hybrid": [
            {
                "product": r.product,
                "score": float(r.score),
                "explanation": r.explanation
            }
            for r in hybrid_recs if r.product
        ],
        "deep": deep_recs,
        "metadata": {
            "active_version": metadata.get("version", "v0.0"),
            "training_time": metadata.get("training_time_seconds", 0.0),
            "best_val_loss": metadata.get("best_val_loss", 0.0),
            "trained_at": metadata.get("trained_at", "N/A"),
            "history": metadata.get("history", {})
        },
        "metrics": metrics
    }

    return APIResponse(
        success=True,
        message="Recommendation model comparison retrieved successfully.",
        data=comparison
    )

