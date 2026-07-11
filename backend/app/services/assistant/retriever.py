import re
from typing import Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.category import Category
from app.models.recommendation import Recommendation
from app.models.review import Review
from app.models.order import Order
from app.models.order_item import OrderItem


class ProductRetriever:
    """Retrieves real database products matching specific intent filters and recommendation outputs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve_products(
        self,
        intent: str,
        query: str,
        user_id: int | None = None,
        context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Query real database products using categories, prices, recommendations, or search queries.
        
        Returns:
            list of dicts containing serialized product attributes.
        """
        stmt = select(Product).where(Product.is_deleted == False, Product.is_active == True)
        
        cleaned_query = query.lower().strip()
        
        # 1. Category extraction
        categories_stmt = select(Category)
        categories_res = await self.db.execute(categories_stmt)
        categories = categories_res.scalars().all()
        
        matched_cat_ids = []
        for cat in categories:
            if cat.name.lower() in cleaned_query:
                matched_cat_ids.append(cat.id)
                
        if matched_cat_ids:
            stmt = stmt.where(Product.category_id.in_(matched_cat_ids))

        # 2. Price filtering
        # Match "under <number>", "below <number>", "less than <number>" or simply digits
        prices = [int(p) for p in re.findall(r'\b\d+[\d,]*\b', cleaned_query.replace(',', ''))]
        if prices:
            target_price = prices[0]
            # Handle currency symbols adjustments if any
            stmt = stmt.where(Product.price <= float(target_price))

        # 3. Handle specific intent queries
        if intent == "trending_products":
            # Sort by total orders or rating
            stmt = stmt.order_by(Product.rating.desc(), Product.price.desc())
        elif intent == "wishlist_based" and user_id is not None:
            # We will return the user's recommendations or high-rating items as a fallback
            stmt = stmt.order_by(Product.rating.desc())
        elif intent == "recommend_for_me" and user_id is not None:
            # Query Recommendations table first
            rec_stmt = (
                select(Product)
                .join(Recommendation, Recommendation.product_id == Product.id)
                .where(Recommendation.user_id == user_id)
                .order_by(Recommendation.score.desc())
                .limit(5)
            )
            rec_res = await self.db.execute(rec_stmt)
            recs = rec_res.scalars().all()
            if recs:
                return [self._serialize_product(p, "Personalized Hybrid Recommender") for p in recs]
        
        # Default fallback string matching if no category was explicitly filtered
        if not matched_cat_ids:
            # Match keywords
            search_terms = [t for t in cleaned_query.split() if len(t) > 2]
            if search_terms:
                or_conds = []
                for term in search_terms:
                    or_conds.append(Product.name.ilike(f"%{term}%"))
                    or_conds.append(Product.brand.ilike(f"%{term}%"))
                if or_conds:
                    stmt = stmt.where(and_(*or_conds))

        # Limit to 5 results
        stmt = stmt.limit(5)
        res = await self.db.execute(stmt)
        products_list = res.scalars().all()
        
        return [self._serialize_product(p, "Database Query Search") for p in products_list]

    def _serialize_product(self, p: Product, engine: str) -> dict[str, Any]:
        return {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "price": float(p.price),
            "rating": float(p.rating) if p.rating else 5.0,
            "image_url": p.image_url,
            "recommendation_engine": engine
        }
