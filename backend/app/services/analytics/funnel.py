from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.order import Order

logger = structlog.get_logger()


class JourneyFunnelService:
    """Computes customer funnel metrics: Visitors -> Views -> Wishlist -> Cart -> Checkout -> Purchase."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversion_funnel(self) -> dict[str, Any]:
        """
        Analyze conversion funnel and drop-off rates using Event records.
        """
        # 1. Total sessions (Visitors)
        stmt_visitors = select(func.count(func.distinct(Event.session_id)))
        visitors_count = (await self.db.execute(stmt_visitors)).scalar() or 0

        # 2. Product Views
        stmt_views = select(func.count(func.distinct(Event.session_id))).where(Event.event_type == "view_item")
        views_count = (await self.db.execute(stmt_views)).scalar() or 0

        # 3. Wishlist additions
        stmt_wish = select(func.count(func.distinct(Event.session_id))).where(Event.event_type == "add_to_wishlist")
        wish_count = (await self.db.execute(stmt_wish)).scalar() or 0

        # 4. Cart additions
        stmt_cart = select(func.count(func.distinct(Event.session_id))).where(Event.event_type == "add_to_cart")
        cart_count = (await self.db.execute(stmt_cart)).scalar() or 0

        # 5. Checkout starts
        stmt_check = select(func.count(func.distinct(Event.session_id))).where(Event.event_type == "start_checkout")
        checkout_count = (await self.db.execute(stmt_check)).scalar() or 0

        # 6. Purchases (completed orders count)
        stmt_purchase = select(func.count(func.distinct(Order.id))).where(Order.status == "confirmed")
        purchase_count = (await self.db.execute(stmt_purchase)).scalar() or 0

        # Ensure cascade levels do not exceed parents
        views_count = min(views_count, visitors_count)
        wish_count = min(wish_count, views_count)
        cart_count = min(cart_count, views_count)
        checkout_count = min(checkout_count, cart_count)
        purchase_count = min(purchase_count, checkout_count)

        # Fallbacks for zero divisions
        def pct(a, b):
            return round((a / b) * 100.0, 2) if b > 0 else 0.0

        # Drop-off rates
        drop_view = pct(visitors_count - views_count, visitors_count)
        drop_wish = pct(views_count - wish_count, views_count)
        drop_cart = pct(views_count - cart_count, views_count)
        drop_checkout = pct(cart_count - checkout_count, cart_count)
        drop_purchase = pct(checkout_count - purchase_count, checkout_count)

        # Abandonment indicators
        cart_abandonment_rate = pct(cart_count - purchase_count, cart_count)
        checkout_completion_rate = pct(purchase_count, checkout_count)

        return {
            "steps": [
                {"name": "Visitors", "count": visitors_count, "drop_off_pct": 0.0},
                {"name": "Product Views", "count": views_count, "drop_off_pct": drop_view},
                {"name": "Wishlist Additions", "count": wish_count, "drop_off_pct": drop_wish},
                {"name": "Cart Additions", "count": cart_count, "drop_off_pct": drop_cart},
                {"name": "Checkout Start", "count": checkout_count, "drop_off_pct": drop_checkout},
                {"name": "Purchase Complete", "count": purchase_count, "drop_off_pct": drop_purchase},
            ],
            "rates": {
                "cart_abandonment_rate": cart_abandonment_rate,
                "checkout_completion_rate": checkout_completion_rate,
            }
        }
