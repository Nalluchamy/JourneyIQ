from decimal import Decimal
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.models.cart_item import CartItem
from app.models.wishlist_item import WishlistItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.review import Review
from app.models.product import Product
from app.models.user import User


class FeatureBuilder:
    """Builds numerical behavior matrices and customer traits for recommendation algorithms."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_user_product_interactions(self) -> dict[tuple[int, int], float]:
        """
        Aggregate user interactions with products into weight scores.
        Weights: View = 1.0, Wishlist = 3.0, Cart = 3.0, Purchase = 5.5, Review/Rating = rating value.
        """
        interactions: dict[tuple[int, int], float] = {}

        # 1. Fetch event views and cart adds
        events_stmt = select(Event).where(
            Event.user_id.isnot(None), Event.product_id.isnot(None)
        )
        events_res = await self.db.execute(events_stmt)
        for event in events_res.scalars().all():
            key = (event.user_id, event.product_id)
            weight = 3.0 if "cart" in event.event_type else 1.0
            interactions[key] = interactions.get(key, 0.0) + weight

        # 2. Fetch Wishlist Items
        wishlist_stmt = select(WishlistItem)
        wishlist_res = await self.db.execute(wishlist_stmt)
        for item in wishlist_res.scalars().all():
            key = (item.user_id, item.product_id)
            interactions[key] = interactions.get(key, 0.0) + 3.0

        # 3. Fetch Cart Items
        cart_stmt = select(CartItem)
        cart_res = await self.db.execute(cart_stmt)
        for item in cart_res.scalars().all():
            key = (item.user_id, item.product_id)
            interactions[key] = interactions.get(key, 0.0) + 3.0

        # 4. Fetch Purchases (Order & OrderItems)
        order_stmt = select(Order).options(selectinload(Order.items))
        order_res = await self.db.execute(order_stmt)
        for order in order_res.scalars().all():
            for item in order.items:
                key = (order.user_id, item.product_id)
                interactions[key] = interactions.get(key, 0.0) + 5.5

        # 5. Fetch Ratings
        reviews_stmt = select(Review)
        reviews_res = await self.db.execute(reviews_stmt)
        for rev in reviews_res.scalars().all():
            key = (rev.user_id, rev.product_id)
            interactions[key] = interactions.get(key, 0.0) + float(rev.rating)

        return interactions

    async def get_user_profiles(self) -> dict[int, dict[str, Any]]:
        """
        Computes user purchasing patterns: Average spend, total purchases, etc.
        """
        profiles: dict[int, dict[str, Any]] = {}
        stmt = select(Order)
        res = await self.db.execute(stmt)
        orders = res.scalars().all()

        for order in orders:
            u_id = order.user_id
            if u_id not in profiles:
                profiles[u_id] = {
                    "total_spend": 0.0,
                    "order_count": 0,
                    "average_spend": 0.0,
                }
            profiles[u_id]["total_spend"] += float(order.total)
            profiles[u_id]["order_count"] += 1

        for u_id, prof in profiles.items():
            if prof["order_count"] > 0:
                prof["average_spend"] = prof["total_spend"] / prof["order_count"]

        return profiles
