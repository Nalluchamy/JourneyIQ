import datetime
import json
import os
from typing import Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.review import Review
from app.models.user import User
from app.models.segment import Segment
from app.models.wishlist_item import WishlistItem
from app.models.cart_item import CartItem
from app.models.payment import Payment
from app.models.event import Event


class ObserverModule:
    """Scans live e-commerce databases and metrics logs to extract telemetry for analysis."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def observe_environment(self) -> dict[str, Any]:
        """
        Queries all tables and logs dynamically to compile business status.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        if self.db.bind.dialect.name == "sqlite":
            now = now.replace(tzinfo=None)
        one_day_ago = now - datetime.timedelta(days=1)
        two_days_ago = now - datetime.timedelta(days=2)
        seven_days_ago = now - datetime.timedelta(days=7)

        # 1. Inventory & Products
        stmt_products = select(Product).where(Product.is_deleted == False, Product.is_active == True)
        res_products = await self.db.execute(stmt_products)
        products = res_products.scalars().all()
        total_products = len(products)
        low_stock_products = [p for p in products if p.stock < 5]
        out_of_stock_products = [p for p in products if p.stock == 0]

        # 2. Orders & Sales
        stmt_orders = select(Order)
        res_orders = await self.db.execute(stmt_orders)
        orders = res_orders.scalars().all()
        total_orders = len(orders)
        pending_orders = len([o for o in orders if o.status == "pending"])
        completed_orders = len([o for o in orders if o.status == "confirmed"])

        # 3. Revenue calculations
        # Today vs Yesterday
        stmt_rev_today = select(func.sum(Order.total)).where(
            and_(Order.status == "confirmed", Order.created_at >= one_day_ago)
        )
        rev_today = (await self.db.execute(stmt_rev_today)).scalar() or 0.0

        stmt_rev_yesterday = select(func.sum(Order.total)).where(
            and_(
                Order.status == "confirmed",
                Order.created_at >= two_days_ago,
                Order.created_at < one_day_ago
            )
        )
        rev_yesterday = (await self.db.execute(stmt_rev_yesterday)).scalar() or 0.0

        # 4. Customers & Segments
        stmt_users = select(User).where(User.is_deleted == False)
        res_users = await self.db.execute(stmt_users)
        users = res_users.scalars().all()
        total_customers = len(users)

        stmt_segments = select(Segment)
        res_segments = await self.db.execute(stmt_segments)
        segments = res_segments.scalars().all()
        
        at_risk_count = len([s for s in segments if s.segment_name.lower() in ("at risk", "slipping")])

        # 5. Reviews & Sentiment
        stmt_reviews = select(Review)
        res_reviews = await self.db.execute(stmt_reviews)
        reviews = res_reviews.scalars().all()
        total_reviews = len(reviews)
        negative_reviews = [r for r in reviews if r.rating <= 2]
        negative_reviews_count = len(negative_reviews)
        positive_pct = 100.0
        if total_reviews > 0:
            positive_reviews = len([r for r in reviews if r.rating >= 4])
            positive_pct = round((positive_reviews / total_reviews) * 100, 1)

        # 6. Wishlist & Cart
        stmt_wishlist = select(func.count(WishlistItem.id))
        total_wishlist_items = (await self.db.execute(stmt_wishlist)).scalar() or 0

        stmt_cart = select(func.count(CartItem.id))
        total_cart_items = (await self.db.execute(stmt_cart)).scalar() or 0

        # Cart abandonment calculation: Carts with items inactive for > 2 hours
        two_hours_ago = now - datetime.timedelta(hours=2)
        stmt_abandoned_carts = select(func.count(func.distinct(CartItem.user_id))).where(
            CartItem.created_at <= two_hours_ago
        )
        abandoned_carts_count = (await self.db.execute(stmt_abandoned_carts)).scalar() or 0

        # 7. AI Chat Usage & Events metrics
        stmt_chat_count = select(func.count(Event.id)).where(
            and_(Event.event_type == "chat_message", Event.timestamp >= one_day_ago)
        )
        chat_queries_today = (await self.db.execute(stmt_chat_count)).scalar() or 0

        # Page views & Product clicks
        stmt_pvs = select(func.count(Event.id)).where(Event.event_type == "page_view")
        total_page_views = (await self.db.execute(stmt_pvs)).scalar() or 0

        stmt_clicks = select(func.count(Event.id)).where(
            Event.event_type.in_(["view_item", "product_click"])
        )
        total_product_clicks = (await self.db.execute(stmt_clicks)).scalar() or 0

        # Recommendation click rates
        stmt_rec_shows = select(func.count(Event.id)).where(Event.event_type == "show_recommendations")
        rec_shows = (await self.db.execute(stmt_rec_shows)).scalar() or 0

        stmt_rec_clicks = select(func.count(Event.id)).where(Event.event_type == "click_recommendation")
        rec_clicks = (await self.db.execute(stmt_rec_clicks)).scalar() or 0
        rec_click_rate = 0.0
        if rec_shows > 0:
            rec_click_rate = round((rec_clicks / rec_shows) * 100, 2)

        # Search trends
        stmt_searches = select(Event.metadata_).where(Event.event_type == "search_query")
        res_searches = await self.db.execute(stmt_searches)
        search_terms = {}
        for row in res_searches.scalars().all():
            if row and "query" in row:
                q = row["query"].lower().strip()
                search_terms[q] = search_terms.get(q, 0) + 1
        popular_searches = sorted(search_terms.items(), key=lambda x: x[1], reverse=True)[:5]

        # Average Session Duration
        stmt_sessions = select(
            Event.session_id,
            func.max(Event.timestamp),
            func.min(Event.timestamp)
        ).group_by(Event.session_id)
        res_sessions = await self.db.execute(stmt_sessions)
        session_diffs = []
        for row in res_sessions.all():
            diff = (row[1] - row[2]).total_seconds()
            session_diffs.append(diff)
        avg_session_duration = round(sum(session_diffs) / len(session_diffs), 1) if session_diffs else 0.0

        # 8. Payment failures
        stmt_failed_payments = select(func.count(Payment.id)).where(
            and_(Payment.status == "failed", Payment.created_at >= one_day_ago)
        )
        failed_payments_today = (await self.db.execute(stmt_failed_payments)).scalar() or 0

        stmt_total_payments = select(func.count(Payment.id)).where(Payment.created_at >= one_day_ago)
        total_payments_today = (await self.db.execute(stmt_total_payments)).scalar() or 0

        payment_failure_rate = 0.0
        if total_payments_today > 0:
            payment_failure_rate = round((failed_payments_today / total_payments_today) * 100, 2)

        # 9. Slow & Fast Selling Products (Last 7 Days)
        stmt_sales_7d = select(
            OrderItem.product_id,
            func.sum(OrderItem.quantity)
        ).join(Order, OrderItem.order_id == Order.id).where(
            and_(Order.status == "confirmed", Order.created_at >= seven_days_ago)
        ).group_by(OrderItem.product_id)
        
        res_sales_7d = await self.db.execute(stmt_sales_7d)
        sales_7d_map = {row[0]: row[1] for row in res_sales_7d.all()}
        
        sorted_sales = sorted(sales_7d_map.items(), key=lambda x: x[1], reverse=True)
        
        # Resolve names
        fast_selling = []
        for p_id, qty in sorted_sales[:3]:
            prod = await self.db.get(Product, p_id)
            if prod:
                fast_selling.append({"name": prod.name, "sales": int(qty)})
                
        # Slow selling are products with zero sales in last 7 days or very low sales
        slow_selling = []
        for p in products:
            qty = sales_7d_map.get(p.id, 0)
            if qty == 0:
                slow_selling.append({"name": p.name, "sales": 0})
        slow_selling = slow_selling[:5]

        # 10. Recommendation model metrics
        precision_at_10 = 0.0
        ndcg = 0.0
        metrics_path = "models/evaluation_metrics.json"
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r") as f:
                    metrics_data = json.load(f)
                    precision_at_10 = metrics_data.get("precision_at_10", 0.0)
                    ndcg = metrics_data.get("ndcg", 0.0)
            except Exception:
                pass

        return {
            "inventory": {
                "total_products": total_products,
                "low_stock_count": len(low_stock_products),
                "low_stock_products": [p.name for p in low_stock_products],
                "out_of_stock_count": len(out_of_stock_products),
                "out_of_stock_products": [p.name for p in out_of_stock_products],
            },
            "orders": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
            },
            "revenue": {
                "today": float(rev_today),
                "yesterday": float(rev_yesterday),
                "drop_pct": round(((rev_yesterday - rev_today) / rev_yesterday) * 100, 2) if rev_yesterday > 0 else 0.0,
            },
            "customers": {
                "total_customers": total_customers,
                "at_risk_count": at_risk_count,
            },
            "reviews": {
                "total_reviews": total_reviews,
                "negative_reviews_count": negative_reviews_count,
                "positive_pct": positive_pct,
            },
            "wishlist": {
                "total_wishlist_items": total_wishlist_items,
            },
            "cart": {
                "total_cart_items": total_cart_items,
                "abandoned_carts_count": abandoned_carts_count,
            },
            "events": {
                "chat_queries_today": chat_queries_today,
                "total_page_views": total_page_views,
                "total_product_clicks": total_product_clicks,
                "rec_click_rate": rec_click_rate,
                "popular_searches": [k for k, v in popular_searches],
                "avg_session_duration": avg_session_duration,
            },
            "payments": {
                "failed_payments_today": failed_payments_today,
                "payment_failure_rate": payment_failure_rate,
            },
            "sales_performance": {
                "fast_selling": fast_selling,
                "slow_selling": slow_selling,
            },
            "recommendation_metrics": {
                "precision_at_10": precision_at_10,
                "ndcg": ndcg,
            }
        }
