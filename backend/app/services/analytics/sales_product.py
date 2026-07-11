import datetime
from decimal import Decimal
from typing import Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.review import Review
from app.models.event import Event


class SalesProductAnalyticsService:
    """Computes Sales and Product analytics metrics, supporting date filters, product statuses, and inventory alerts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_date_range_filter(self, range_name: str, start_date: datetime.datetime | None = None, end_date: datetime.datetime | None = None) -> tuple[datetime.datetime, datetime.datetime]:
        """Calculates start and end datetime limits for date range filters."""
        now = datetime.datetime.now(datetime.timezone.utc)
        today_start = datetime.datetime.combine(now.date(), datetime.time.min, tzinfo=datetime.timezone.utc)

        if range_name == "today":
            return today_start, now
        elif range_name == "yesterday":
            yest_start = today_start - datetime.timedelta(days=1)
            yest_end = datetime.datetime.combine(yest_start.date(), datetime.time.max, tzinfo=datetime.timezone.utc)
            return yest_start, yest_end
        elif range_name == "last_7_days":
            return now - datetime.timedelta(days=7), now
        elif range_name == "last_30_days":
            return now - datetime.timedelta(days=30), now
        elif range_name == "this_month":
            month_start = today_start.replace(day=1)
            return month_start, now
        elif range_name == "custom" and start_date and end_date:
            s_date = start_date if start_date.tzinfo else start_date.replace(tzinfo=datetime.timezone.utc)
            e_date = end_date if end_date.tzinfo else end_date.replace(tzinfo=datetime.timezone.utc)
            return s_date, e_date
        
        # Default fallback to last 30 days
        return now - datetime.timedelta(days=30), now

    async def get_sales_analytics(self, range_name: str, start_date: datetime.datetime | None = None, end_date: datetime.datetime | None = None) -> dict[str, Any]:
        """Calculate total sales summary and timeline chart data."""
        start_dt, end_dt = self.get_date_range_filter(range_name, start_date, end_date)

        # Query orders in date range
        orders_stmt = (
            select(Order)
            .where(
                and_(
                    Order.created_at >= start_dt,
                    Order.created_at <= end_dt
                )
            )
            .options(selectinload(Order.items), selectinload(Order.coupon_usages))
        )
        res = await self.db.execute(orders_stmt)
        orders = res.scalars().all()

        confirmed_orders = [o for o in orders if o.status == "confirmed"]
        total_revenue = sum(float(o.total) for o in confirmed_orders)
        order_count = len(confirmed_orders)
        aov = total_revenue / order_count if order_count > 0 else 0.0

        # Coupon usage rate
        orders_with_coupons = [o for o in confirmed_orders if len(o.coupon_usages) > 0]
        coupon_usage_rate = (len(orders_with_coupons) / order_count * 100.0) if order_count > 0 else 0.0

        # Payment success rate
        successful_payments = len(confirmed_orders)
        total_attempts = len(orders)
        payment_success_rate = (successful_payments / total_attempts * 100.0) if total_attempts > 0 else 100.0

        # Timeline chart data (grouped by date)
        timeline_data: dict[str, dict[str, Any]] = {}
        for o in confirmed_orders:
            # Format date key e.g. YYYY-MM-DD
            date_key = o.created_at.strftime("%Y-%m-%d")
            if date_key not in timeline_data:
                timeline_data[date_key] = {"date": date_key, "revenue": 0.0, "orders": 0}
            timeline_data[date_key]["revenue"] += float(o.total)
            timeline_data[date_key]["orders"] += 1

        chart_list = sorted(timeline_data.values(), key=lambda x: x["date"])

        # Calculate Yesterday's comparative stats for Executive summary
        now = datetime.datetime.now(datetime.timezone.utc)
        yesterday_start = datetime.datetime.combine(now.date() - datetime.timedelta(days=1), datetime.time.min, tzinfo=datetime.timezone.utc)
        yesterday_end = datetime.datetime.combine(now.date() - datetime.timedelta(days=1), datetime.time.max, tzinfo=datetime.timezone.utc)

        stmt_yesterday = select(Order).where(Order.status == "confirmed", Order.created_at >= yesterday_start, Order.created_at <= yesterday_end)
        yesterday_orders = (await self.db.execute(stmt_yesterday)).scalars().all()
        yesterday_revenue = sum(float(o.total) for o in yesterday_orders)
        yesterday_count = len(yesterday_orders)

        # Today's stats
        today_start = datetime.datetime.combine(now.date(), datetime.time.min, tzinfo=datetime.timezone.utc)
        stmt_today = select(Order).where(Order.status == "confirmed", Order.created_at >= today_start)
        today_orders = (await self.db.execute(stmt_today)).scalars().all()
        today_revenue = sum(float(o.total) for o in today_orders)
        today_count = len(today_orders)

        # Revenue delta %
        rev_delta = 0.0
        if yesterday_revenue > 0:
            rev_delta = ((today_revenue - yesterday_revenue) / yesterday_revenue) * 100.0
        elif today_revenue > 0:
            rev_delta = 100.0

        orders_delta = 0.0
        if yesterday_count > 0:
            orders_delta = ((today_count - yesterday_count) / yesterday_count) * 100.0
        elif today_count > 0:
            orders_delta = 100.0

        # Returning customer rate
        stmt_cust = select(Order.user_id, func.count(Order.id)).where(Order.status == "confirmed").group_by(Order.user_id)
        cust_res = await self.db.execute(stmt_cust)
        rows = cust_res.all()
        returning_customers = len([r for r in rows if r[1] > 1])
        total_customers = len(rows)
        returning_rate = (returning_customers / total_customers * 100.0) if total_customers > 0 else 0.0

        return {
            "summary": {
                "total_revenue": round(total_revenue, 2),
                "order_count": order_count,
                "average_order_value": round(aov, 2),
                "coupon_usage_rate": round(coupon_usage_rate, 2),
                "payment_success_rate": round(payment_success_rate, 2),
                "today_revenue": round(today_revenue, 2),
                "today_revenue_delta": round(rev_delta, 1),
                "today_orders": today_count,
                "today_orders_delta": round(orders_delta, 1),
                "returning_customer_rate": round(returning_rate, 1),
            },
            "timeline": chart_list
        }

    async def get_product_analytics(self) -> dict[str, Any]:
        """Compute metrics for Top Selling, Lowest Selling, and Inventory Risk Alerts."""
        # Fetch active products
        prod_stmt = select(Product).where(Product.is_deleted == False)
        products = (await self.db.execute(prod_stmt)).scalars().all()
        products_map = {p.id: p for p in products}

        # 1. Sales counts per product
        stmt_sales = (
            select(OrderItem.product_id, func.sum(OrderItem.quantity).label("sales"))
            .group_by(OrderItem.product_id)
        )
        sales_res = await self.db.execute(stmt_sales)
        sales_data = {row[0]: int(row[1]) for row in sales_res.all()}

        # 2. Ratings per product
        stmt_ratings = (
            select(Review.product_id, func.avg(Review.rating).label("avg_rating"))
            .group_by(Review.product_id)
        )
        ratings_res = await self.db.execute(stmt_ratings)
        ratings_data = {row[0]: float(row[1]) for row in ratings_res.all()}

        # 3. Trending views (views in last 7 days)
        seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        stmt_trending = (
            select(Event.product_id, func.count(Event.id).label("views"))
            .where(Event.event_type == "view_item", Event.timestamp >= seven_days_ago)
            .group_by(Event.product_id)
        )
        trend_res = await self.db.execute(stmt_trending)
        trend_data = {row[0]: int(row[1]) for row in trend_res.all()}

        # Compile product lists
        product_stats = []
        for p in products:
            sales = sales_data.get(p.id, 0)
            rating = ratings_data.get(p.id, 0.0)
            views = trend_data.get(p.id, 0)

            product_stats.append({
                "product_id": p.id,
                "name": p.name,
                "brand": p.brand,
                "stock": p.stock,
                "price": float(p.price),
                "sales": sales,
                "rating": round(rating, 1),
                "views": views
            })

        # Top selling (sales desc)
        top_selling = sorted(product_stats, key=lambda x: x["sales"], reverse=True)[:10]

        # Lowest selling (sales asc)
        lowest_selling = sorted(product_stats, key=lambda x: x["sales"])[:10]

        # Highest rated (rating desc, min 1 sale or rating > 0)
        highest_rated = sorted([p for p in product_stats if p["rating"] > 0], key=lambda x: x["rating"], reverse=True)[:10]

        # Trending (views desc)
        trending = sorted(product_stats, key=lambda x: x["views"], reverse=True)[:10]

        # 4. Inventory Alerts
        inventory_alerts = []
        for p in products:
            sales_7_days = trend_data.get(p.id, 0) # proxy for velocity or map from order items
            # Low stock
            if 0 < p.stock <= 5:
                inventory_alerts.append({
                    "product_id": p.id,
                    "name": p.name,
                    "brand": p.brand,
                    "stock": p.stock,
                    "alert_type": "Low Stock",
                    "priority": "HIGH",
                    "message": f"Only {p.stock} units of {p.name} remaining.",
                    "recommendation": "Restock immediately to prevent stockouts."
                })
            elif p.stock == 0:
                inventory_alerts.append({
                    "product_id": p.id,
                    "name": p.name,
                    "brand": p.brand,
                    "stock": p.stock,
                    "alert_type": "Out of Stock",
                    "priority": "HIGH",
                    "message": f"{p.name} is completely out of stock.",
                    "recommendation": "Urgent restock required."
                })

            # Fast selling (views/sales > 10 in 7 days)
            if sales_7_days >= 10 and p.stock <= 20:
                inventory_alerts.append({
                    "product_id": p.id,
                    "name": p.name,
                    "brand": p.brand,
                    "stock": p.stock,
                    "alert_type": "Fast Selling",
                    "priority": "MEDIUM",
                    "message": f"{p.name} is selling rapidly ({sales_7_days} recent views).",
                    "recommendation": "Increase order quantities for the next shipment."
                })

            # Dead inventory (stock > 10 and 0 sales overall/30 days)
            p_sales = sales_data.get(p.id, 0)
            if p_sales == 0 and p.stock > 10:
                inventory_alerts.append({
                    "product_id": p.id,
                    "name": p.name,
                    "brand": p.brand,
                    "stock": p.stock,
                    "alert_type": "Dead Inventory",
                    "priority": "LOW",
                    "message": f"{p.name} has had zero sales recently with high stock ({p.stock} units).",
                    "recommendation": "Consider markdown promotion or bundle deal to clear shelf space."
                })

        return {
            "top_selling": top_selling,
            "lowest_selling": lowest_selling,
            "highest_rated": highest_rated,
            "trending": trending,
            "inventory_alerts": inventory_alerts
        }
