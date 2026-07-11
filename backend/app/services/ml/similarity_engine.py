import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.review import Review


class SimilarityEngine:
    """Computes similarity vectors and indexes for products and user habits."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_content_similarity(self, target_product: Product, candidate_products: list[Product]) -> list[tuple[Product, float]]:
        """
        Compare target product against list of candidates based on:
        Category (50% weight), Brand (30% weight), Price (20% weight).
        """
        scores: list[tuple[Product, float]] = []
        target_price = float(target_product.price)

        for prod in candidate_products:
            if prod.id == target_product.id:
                continue

            # Category similarity
            cat_score = 1.0 if prod.category_id == target_product.category_id else 0.0

            # Brand similarity
            brand_score = 0.0
            if prod.brand and target_product.brand:
                brand_score = 1.0 if prod.brand.strip().lower() == target_product.brand.strip().lower() else 0.0

            # Price similarity
            prod_price = float(prod.price)
            max_price = max(target_price, prod_price, 1.0)
            price_score = 1.0 - (abs(target_price - prod_price) / max_price)

            # Combined weighted score
            similarity = (cat_score * 0.5) + (brand_score * 0.3) + (price_score * 0.2)
            scores.append((prod, similarity))

        # Sort descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def compute_collaborative_similarities(
        self,
        interactions: dict[tuple[int, int], float],
        all_user_ids: list[int],
    ) -> dict[tuple[int, int], float]:
        """
        Computes cosine similarities between users based on overlapping product interaction weights.
        Returns mapping: (user_id_1, user_id_2) -> similarity_score
        """
        # Represent users as sparse vectors: user_id -> {product_id: weight}
        user_vectors: dict[int, dict[int, float]] = {}
        for (u_id, p_id), weight in interactions.items():
            if u_id not in user_vectors:
                user_vectors[u_id] = {}
            user_vectors[u_id][p_id] = weight

        # Precompute vector magnitudes (norms)
        norms: dict[int, float] = {}
        for u_id, vec in user_vectors.items():
            norms[u_id] = math.sqrt(sum(w ** 2 for w in vec.values()))

        similarities: dict[tuple[int, int], float] = {}
        n_users = len(all_user_ids)

        for i in range(n_users):
            u1 = all_user_ids[i]
            if u1 not in user_vectors:
                continue
            for j in range(i + 1, n_users):
                u2 = all_user_ids[j]
                if u2 not in user_vectors:
                    continue

                # Compute dot product on common product keys
                common_prods = set(user_vectors[u1].keys()) & set(user_vectors[u2].keys())
                if not common_prods:
                    continue

                dot_product = sum(user_vectors[u1][p] * user_vectors[u2][p] for p in common_prods)
                norm_product = norms[u1] * norms[u2]

                similarity = dot_product / norm_product if norm_product > 0 else 0.0
                if similarity > 0:
                    similarities[(u1, u2)] = similarity
                    similarities[(u2, u1)] = similarity

        return similarities

    async def compute_popularity_metrics(self) -> dict[str, list[tuple[int, float]]]:
        """
        Computes general popularity listings:
        - "best_selling": quantity of items ordered.
        - "highest_rated": average review rating (min 1 review).
        - "trending": views count in recent events.
        """
        results: dict[str, list[tuple[int, float]]] = {
            "best_selling": [],
            "highest_rated": [],
            "trending": [],
        }

        # 1. Best selling
        bs_stmt = (
            select(OrderItem.product_id, func.sum(OrderItem.quantity).label("sales"))
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(20)
        )
        bs_res = await self.db.execute(bs_stmt)
        for row in bs_res.all():
            results["best_selling"].append((row[0], float(row[1])))

        # 2. Highest rated
        hr_stmt = (
            select(Review.product_id, func.avg(Review.rating).label("avg_rating"))
            .group_by(Review.product_id)
            .order_by(func.avg(Review.rating).desc())
            .limit(20)
        )
        hr_res = await self.db.execute(hr_stmt)
        for row in hr_res.all():
            results["highest_rated"].append((row[0], float(row[1])))

        # 3. Trending (views from Events)
        trend_stmt = (
            select(Event.product_id, func.count(Event.id).label("views"))
            .where(Event.event_type == "view_item", Event.product_id.isnot(None))
            .group_by(Event.product_id)
            .order_by(func.count(Event.id).desc())
            .limit(20)
        )
        trend_res = await self.db.execute(trend_stmt)
        for row in trend_res.all():
            results["trending"].append((row[0], float(row[1])))

        return results
