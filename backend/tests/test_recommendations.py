import datetime
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models import Category, Product, User, Event, Review, Order, OrderItem, Recommendation
from app.services.ml.feature_builder import FeatureBuilder
from app.services.ml.similarity_engine import SimilarityEngine
from app.services.ml.hybrid_ranker import HybridRanker
from app.services.ml.recommendation_service import RecommendationService


@pytest.mark.asyncio
async def test_recommendation_engine_pipeline(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # 1. Seed Categories & Products & Users
    category = Category(name="Electronics", slug="electronics")
    db_session.add(category)
    await db_session.flush()

    prod1 = Product(
        category_id=category.id,
        name="Apple iPhone 15",
        slug="iphone-15",
        brand="Apple",
        price=Decimal("999.00"),
        stock=10,
        is_active=True,
    )
    prod2 = Product(
        category_id=category.id,
        name="Samsung Galaxy S24",
        slug="galaxy-s24",
        brand="Samsung",
        price=Decimal("899.00"),
        stock=10,
        is_active=True,
    )
    prod3 = Product(
        category_id=category.id,
        name="Sony Headphones",
        slug="sony-headphones",
        brand="Sony",
        price=Decimal("349.00"),
        stock=15,
        is_active=True,
    )
    db_session.add_all([prod1, prod2, prod3])
    await db_session.flush()

    user_a = User(email="usera@example.com", password_hash="pw", full_name="User A", role="customer", is_verified=True)
    user_b = User(email="userb@example.com", password_hash="pw", full_name="User B", role="customer", is_verified=True)
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    # 2. Seed interaction data
    # User A views iPhone
    import uuid
    event1 = Event(user_id=user_a.id, session_id=uuid.uuid4(), event_type="view_item", product_id=prod1.id)
    # User B views iPhone and rates Galaxy S24
    event2 = Event(user_id=user_b.id, session_id=uuid.uuid4(), event_type="view_item", product_id=prod1.id)
    review = Review(user_id=user_b.id, product_id=prod2.id, rating=5, review="Great!")
    db_session.add_all([event1, event2, review])
    await db_session.commit()

    # 3. Test Feature Builder
    builder = FeatureBuilder(db_session)
    interactions = await builder.build_user_product_interactions()
    assert (user_a.id, prod1.id) in interactions
    assert interactions[(user_a.id, prod1.id)] >= 1.0

    # 4. Test Similarity Engine
    engine = SimilarityEngine(db_session)
    candidates = [prod2, prod3]
    sims = await engine.compute_content_similarity(prod1, candidates)
    # Samsung is in same category and price is closer to iPhone than Sony headphones
    assert sims[0][0].id == prod2.id

    # 5. Test Recommendation Service Run
    service = RecommendationService(db_session)
    await service.compute_and_persist_recommendations()

    # Verify recommendations saved in database
    recs_stmt = select(Recommendation).where(Recommendation.user_id == user_a.id)
    recs_res = await db_session.execute(recs_stmt)
    recs = recs_res.scalars().all()
    assert len(recs) > 0

    # 6. Test GET API Endpoints
    token = create_access_token(user_a.id)
    headers = {"Authorization": f"Bearer {token}", "x-session-id": "33333333-4444-5555-6666-777777777777"}

    # Recommendations Personalized
    res_recs = await client.get("/api/v1/recommendations", headers=headers)
    assert res_recs.status_code == 200
    assert len(res_recs.json()["data"]) > 0
    assert "explanation" in res_recs.json()["data"][0]

    # Similar Products API
    res_sim = await client.get(f"/api/v1/products/{prod1.id}/similar", headers=headers)
    assert res_sim.status_code == 200
    assert len(res_sim.json()["data"]) > 0

    # Trending API
    res_trend = await client.get("/api/v1/recommendations/trending", headers=headers)
    assert res_trend.status_code == 200
    assert len(res_trend.json()["data"]) > 0

    # Popular API
    res_pop = await client.get("/api/v1/recommendations/popular", headers=headers)
    assert res_pop.status_code == 200
    assert len(res_pop.json()["data"]) > 0
