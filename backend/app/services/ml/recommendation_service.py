import datetime
import structlog
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.recommendation import Recommendation
from app.services.ml.feature_builder import FeatureBuilder
from app.services.ml.similarity_engine import SimilarityEngine
from app.services.ml.hybrid_ranker import HybridRanker
from app.services.ml.evaluation import RecommenderEvaluator

logger = structlog.get_logger()


class RecommendationService:
    """Orchestrates features extraction, similarity computations, hybrid ranking, and DB persistence."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_builder = FeatureBuilder(db)
        self.similarity_engine = SimilarityEngine(db)
        self.ranker = HybridRanker()

    async def compute_and_persist_recommendations(self) -> None:
        """
        Runs daily recomputation pipeline.
        1. Fetch all users, products, orders.
        2. Extact user interactions weights.
        3. Build product content similarity lists.
        4. Compute collaborative similarities.
        5. For each user, rank products, assign explanations, and store.
        6. Compute precision / recall and evaluate metrics.
        """
        logger.info("Starting daily recommendation recomputation pipeline")

        # 1. Fetch data
        users_stmt = select(User).where(User.is_deleted == False)
        users = (await self.db.execute(users_stmt)).scalars().all()
        user_ids = [u.id for u in users]

        products_stmt = select(Product).where(Product.is_deleted == False, Product.is_active == True)
        products = (await self.db.execute(products_stmt)).scalars().all()
        product_ids = [p.id for p in products]

        # Extract product names map for explainability reasons
        purchased_names = {p.id: p.name for p in products}

        # 2. Extract features
        interactions = await self.feature_builder.build_user_product_interactions()

        # 3. Compute similarities
        # Precompute content similarity matrix for all products
        content_similarities: dict[int, list[tuple[int, float]]] = {}
        for target in products:
            sims = await self.similarity_engine.compute_content_similarity(target, products)
            content_similarities[target.id] = [(p.id, score) for p, score in sims]

        # Compute collaborative similarities
        user_similarities = self.similarity_engine.compute_collaborative_similarities(interactions, user_ids)

        # Get popularity metrics
        pop_metrics = await self.similarity_engine.compute_popularity_metrics()

        # Get past purchases for each user (to exclude from recommendations and build validation ground truth)
        orders_stmt = select(Order).options(selectinload(Order.items))
        orders = (await self.db.execute(orders_stmt)).scalars().all()
        
        user_purchases: dict[int, set[int]] = {u_id: set() for u_id in user_ids}
        for order in orders:
            if order.user_id in user_purchases:
                for item in order.items:
                    user_purchases[order.user_id].add(item.product_id)

        # 4. Generate recommendations & clear old records
        await self.db.execute(delete(Recommendation))
        
        recommendations_map: dict[int, list[int]] = {}
        ground_truth: dict[int, list[int]] = {}

        for user in users:
            purchases = user_purchases.get(user.id, set())
            ranked = self.ranker.rank_for_user(
                user_id=user.id,
                products=products,
                user_interactions=interactions,
                user_similarities=user_similarities,
                content_similarities=content_similarities,
                popularity_metrics=pop_metrics,
                purchased_product_names=purchased_names,
                user_purchases=purchases,
            )

            # Store top 10 recommendations per user in database
            top_recs = ranked[:10]
            recommendations_map[user.id] = [r["product_id"] for r in top_recs]

            # Collect actual interactions/purchases as ground truth for metrics
            interacted = [p_id for (u_id, p_id), w in interactions.items() if u_id == user.id and w > 0]
            if interacted:
                ground_truth[user.id] = interacted

            for item in top_recs:
                rec = Recommendation(
                    user_id=user.id,
                    product_id=item["product_id"],
                    score=item["score"],
                    explanation=item["explanation"],
                )
                self.db.add(rec)

        await self.db.commit()

        # 5. Model evaluation metrics logging
        if ground_truth:
            RecommenderEvaluator.evaluate(
                recommendations=recommendations_map,
                ground_truth=ground_truth,
                all_product_ids=product_ids,
                k=5
            )

        logger.info("Daily recommendations pipeline completed and persisted successfully")
