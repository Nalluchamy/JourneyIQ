import datetime
from typing import Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.product import Product
from app.models.review import Review
from app.models.payment import Payment
from app.models.event import Event
from app.models.agent_action import AgentAction
from app.models.agent_learning import AgentLearning


class CopilotSqlBuilder:
    """Retrieves dynamic, live metrics from database tables for the copilot services."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_revenue_timeline(self, days: int = 7) -> list[dict[str, Any]]:
        """Fetch daily revenue summaries over the last N days."""
        now = datetime.datetime.utcnow()
        if self.db.bind.dialect.name == "sqlite":
            now = now.replace(tzinfo=None)
        start_date = now - datetime.timedelta(days=days)

        # For sqlite vs postgres compatible grouping
        stmt = (
            select(
                func.date(Order.created_at).label("date"),
                func.sum(Order.total).label("revenue"),
                func.count(Order.id).label("orders")
            )
            .where(
                and_(
                    Order.status == "confirmed",
                    Order.created_at >= start_date
                )
            )
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at).asc())
        )
        res = await self.db.execute(stmt)
        return [{"date": str(row[0]), "revenue": float(row[1] or 0.0), "orders": int(row[2] or 0)} for row in res.all()]

    async def get_inventory_health(self) -> dict[str, Any]:
        """Fetch current active stock levels and compile alerts."""
        stmt = select(Product).where(Product.is_deleted == False, Product.is_active == True)
        res = await self.db.execute(stmt)
        products = res.scalars().all()
        
        total = len(products)
        low_stock = [p for p in products if p.stock < 5]
        out_of_stock = [p for p in products if p.stock == 0]
        
        # Inventory health % = percent of products in-stock (stock > 0)
        health_pct = round(((total - len(out_of_stock)) / total * 100.0), 1) if total > 0 else 100.0

        return {
            "total_products": total,
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
            "health_pct": health_pct,
            "low_stock_details": [{"name": p.name, "stock": p.stock, "price": float(p.price)} for p in low_stock],
            "out_of_stock_details": [{"name": p.name, "price": float(p.price)} for p in out_of_stock]
        }

    async def get_customer_satisfaction(self) -> dict[str, Any]:
        """Fetch average sentiments score and breakdown percentages from product reviews."""
        stmt = select(Review)
        res = await self.db.execute(stmt)
        reviews = res.scalars().all()
        
        total = len(reviews)
        if total == 0:
            return {"satisfaction_score": 100.0, "positive_pct": 100.0, "neutral_pct": 0.0, "negative_pct": 0.0, "total_reviews": 0}

        positive = len([r for r in reviews if r.rating >= 4])
        neutral = len([r for r in reviews if r.rating == 3])
        negative = len([r for r in reviews if r.rating <= 2])

        pos_pct = round((positive / total) * 100.0, 1)
        neu_pct = round((neutral / total) * 100.0, 1)
        neg_pct = round((negative / total) * 100.0, 1)

        # Satisfaction index = average reviews rating scaled to 100
        avg_rating = sum([r.rating for r in reviews]) / total
        satisfaction_score = round((avg_rating / 5.0) * 100.0, 1)

        return {
            "satisfaction_score": satisfaction_score,
            "positive_pct": pos_pct,
            "neutral_pct": neu_pct,
            "negative_pct": neg_pct,
            "total_reviews": total
        }

    async def get_payment_failures(self) -> dict[str, Any]:
        """Calculate recent checkout payment failures and failure rate percentage."""
        now = datetime.datetime.utcnow()
        if self.db.bind.dialect.name == "sqlite":
            now = now.replace(tzinfo=None)
        one_day_ago = now - datetime.timedelta(days=1)

        stmt_failed = select(func.count(Payment.id)).where(
            and_(Payment.status == "failed", Payment.created_at >= one_day_ago)
        )
        failed_count = (await self.db.execute(stmt_failed)).scalar() or 0

        stmt_total = select(func.count(Payment.id)).where(Payment.created_at >= one_day_ago)
        total_count = (await self.db.execute(stmt_total)).scalar() or 0

        failure_rate = round((failed_count / total_count * 100.0), 2) if total_count > 0 else 0.0

        return {
            "failed_payments_today": failed_count,
            "total_payments_today": total_count,
            "payment_failure_rate": failure_rate
        }

    async def get_abandoned_carts_count(self) -> int:
        """Fetch count of shopping carts abandoned (inactive for > 2 hours)."""
        now = datetime.datetime.utcnow()
        if self.db.bind.dialect.name == "sqlite":
            now = now.replace(tzinfo=None)
        two_hours_ago = now - datetime.timedelta(hours=2)

        # Assuming Event table tracks start_checkout and cart activities
        stmt = select(func.count(func.distinct(Event.session_id))).where(
            and_(
                Event.event_type == "start_checkout",
                Event.timestamp <= two_hours_ago,
                Event.timestamp >= (now - datetime.timedelta(days=1))
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar() or 0
