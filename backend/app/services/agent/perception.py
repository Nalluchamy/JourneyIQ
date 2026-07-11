from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.review import Review
from app.models.order import Order
from app.models.segment import Segment
from app.services.analytics.funnel import JourneyFunnelService
from app.services.nlp.review_analyzer import ReviewAnalyzerService


class PerceptionModule:
    """Scans and parses the store database state to feed into the Agent's reasoning engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.funnel_service = JourneyFunnelService(db)
        self.review_service = ReviewAnalyzerService(db)

    async def observe_environment(self) -> dict[str, Any]:
        """
        Gathers metric telemetry: stock alert triggers, churn segments, funnel drop-offs, and reviews sentiment.
        """
        # 1. Check stock out levels
        stock_stmt = select(Product).where(Product.is_deleted == False, Product.is_active == True, Product.stock <= 5)
        stock_alerts = (await self.db.execute(stock_stmt)).scalars().all()
        stock_count = len(stock_alerts)

        # 2. Check segment counts
        segment_stmt = select(Segment.segment_name, func.count(Segment.id)).group_by(Segment.segment_name)
        segments_res = await self.db.execute(segment_stmt)
        segments_map = {row[0]: row[1] for row in segments_res.all()}

        # 3. Check conversion funnel rates
        funnel = await self.funnel_service.get_conversion_funnel()
        completion_rate = funnel["rates"]["checkout_completion_rate"]
        abandonment_rate = funnel["rates"]["cart_abandonment_rate"]

        # 4. Check sentiment
        sentiment = await self.review_service.analyze_all_reviews()

        return {
            "low_stock_count": stock_count,
            "low_stock_products": [p.name for p in stock_alerts[:3]],
            "segments_distribution": segments_map,
            "checkout_completion_rate": completion_rate,
            "cart_abandonment_rate": abandonment_rate,
            "overall_sentiment_pct": sentiment["positive_pct"],
            "top_complaint": sentiment["top_complaints"][0] if sentiment["top_complaints"] else "None",
            "trending_keywords": sentiment["top_keywords"]
        }
