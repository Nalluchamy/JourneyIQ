from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.order import Order
from app.models.product import Product
from app.services.analytics.customer_intelligence import CustomerIntelligenceService
from app.services.analytics.funnel import JourneyFunnelService


class AIInsightsService:
    """Generates natural language business insights with Priority flags (HIGH, MEDIUM, LOW) and Actionable suggestions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.intel_service = CustomerIntelligenceService(db)
        self.funnel_service = JourneyFunnelService(db)

    async def generate_business_insights(self) -> list[dict[str, Any]]:
        """
        Dynamically analyzes database trends to compile high-impact business insights.
        """
        insights = []

        # 1. Churn Insights (HIGH Priority)
        try:
            intel = await self.intel_service.calculate_rfm_and_segmentation()
            high_churn_count = len([c for c in intel if c["churn"]["risk_level"] == "High"])
            if high_churn_count > 0:
                insights.append({
                    "priority": "HIGH",
                    "title": "Customer Retention Warning",
                    "insight": f"{high_churn_count} customers are at high risk of churning soon.",
                    "action": "Offer a targeted 15% discount coupon to win them back."
                })
        except Exception:
            pass

        # 2. Funnel / Cart Abandonment Insights (HIGH/MEDIUM Priority)
        try:
            funnel = await self.funnel_service.get_conversion_funnel()
            abandon_rate = funnel["rates"]["cart_abandonment_rate"]
            if abandon_rate > 50.0:
                insights.append({
                    "priority": "HIGH",
                    "title": "Severe Cart Abandonment",
                    "insight": f"Cart abandonment rate is currently at {abandon_rate}%.",
                    "action": "Enable automatic abandoned cart recovery emails and verify checkout loading speeds."
                })
            elif abandon_rate > 30.0:
                insights.append({
                    "priority": "MEDIUM",
                    "title": "Moderate Cart Abandonment",
                    "insight": f"Cart abandonment is sitting at {abandon_rate}%.",
                    "action": "Offer free shipping thresholds to encourage checkout completions."
                })
        except Exception:
            pass

        # 3. Peak Shopping Hours (MEDIUM Priority)
        try:
            orders_stmt = select(Order.created_at).where(Order.status == "confirmed")
            res = await self.db.execute(orders_stmt)
            times = res.scalars().all()

            if times:
                hours = [t.hour for t in times]
                # Find most frequent hour
                peak_hour = max(set(hours), key=hours.count)

                # Format explanation label
                start_h = peak_hour
                end_h = (peak_hour + 3) % 24

                # Translate 24h to AM/PM readable format
                def fmt_h(h):
                    return f"{12 if h % 12 == 0 else h % 12} {'PM' if h >= 12 else 'AM'}"

                insights.append({
                    "priority": "MEDIUM",
                    "title": "Peak Shopping Traffic",
                    "insight": f"Most customer orders are placed between {fmt_h(start_h)} and {fmt_h(end_h)}.",
                    "action": f"Schedule promotional newsletters and email blasts around {fmt_h(start_h)} to capture active buyers."
                })
        except Exception:
            pass

        # 4. Top Category Revenue (LOW Priority)
        try:
            # Query category performance joining orders, items, products, category
            stmt = (
                select(Category.name, func.sum(Order.total))
                .select_from(Order)
                .join(Order.items)
                .join(Product)
                .join(Category)
                .where(Order.status == "confirmed")
                .group_by(Category.name)
                .order_by(func.sum(Order.total).desc())
                .limit(1)
            )
            cat_res = await self.db.execute(stmt)
            top_cat = cat_res.first()

            if top_cat:
                insights.append({
                    "priority": "LOW",
                    "title": "Top Category Performer",
                    "insight": f"The '{top_cat[0]}' category generated the highest share of sales revenue.",
                    "action": "Expand product catalog options and increase digital marketing budget for this category."
                })
        except Exception:
            pass

        # Fallback if no data is available
        if not insights:
            insights.append({
                "priority": "LOW",
                "title": "Initial Dashboard Build",
                "insight": "Platform is compiling initial customer intelligence logs.",
                "action": "Place orders or view store listings to populate analytics reports."
            })

        return insights
