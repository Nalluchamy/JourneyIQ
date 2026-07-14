import re
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics.sales_product import SalesProductAnalyticsService
from app.services.analytics.customer_intelligence import CustomerIntelligenceService
from app.services.analytics.insights import AIInsightsService
from app.services.copilot.sql_builder import CopilotSqlBuilder


class CopilotQueryEngine:
    """Translates natural language retail business questions into database data queries."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sql_builder = CopilotSqlBuilder(db)
        self.sales_service = SalesProductAnalyticsService(db)
        self.intel_service = CustomerIntelligenceService(db)
        self.insights_service = AIInsightsService(db)

    async def execute_query(self, message: str) -> dict[str, Any]:
        """
        Parses the query text, determines intent, executes database calls,
        and returns a structured data context mapping.
        """
        msg = message.lower().strip()

        # Intent Classification & Routing
        if any(kw in msg for kw in ["revenue decrease", "revenue drop", "why did revenue", "sales drop"]):
            return await self._handle_revenue_drop()
            
        elif any(kw in msg for kw in ["restock", "low stock", "run out of stock", "inventory issue"]):
            return await self._handle_restock_check()
            
        elif any(kw in msg for kw in ["churn", "slipping customers", "at risk customers"]):
            return await self._handle_churn_check()
            
        elif any(kw in msg for kw in ["trending", "popular products", "best sellers"]):
            return await self._handle_trending_products()
            
        elif any(kw in msg for kw in ["recommendations decreasing", "recommendation drop", "ncf drop", "recommendation engine accuracy"]):
            return await self._handle_recommendations_degradation()
            
        elif any(kw in msg for kw in ["satisfaction", "sentiment", "reviews", "csat", "customer complaints"]):
            return await self._handle_sentiment_check()
            
        elif any(kw in msg for kw in ["slow moving", "dead stock", "unsold products"]):
            return await self._handle_slow_moving()
            
        elif any(kw in msg for kw in ["kpi summary", "today's kpi", "business overview", "dashboard metrics"]):
            return await self._handle_kpi_summary()
            
        elif any(kw in msg for kw in ["campaign", "promotions", "coupon performance", "best campaigns"]):
            return await self._handle_campaigns_performance()
            
        elif any(kw in msg for kw in ["report", "generate report", "executive report"]):
            return await self._handle_report_generation()

        # Default query handler fallback (general search catalog metrics)
        return await self._handle_default_analytics()

    async def _handle_revenue_drop(self) -> dict[str, Any]:
        sales = await self.sales_service.get_sales_analytics("last_30_days")
        summary = sales.get("summary", {})
        
        # Pull products velocity to find drops
        prods = await self.sales_service.get_product_analytics()
        lowest_sellers = prods.get("lowest_selling", [])[:5]

        # Abandoned cart count
        abandoned_carts = await self.sql_builder.get_abandoned_carts_count()

        return {
            "intent": "REVENUE_DROP",
            "sources": ["Orders", "Sales Analytics", "Cart Activity"],
            "data": {
                "revenue_drop_pct": float(summary.get("revenue_change_pct", 0.0)),
                "total_revenue_today": float(summary.get("total_revenue", 0.0)),
                "orders_count": int(summary.get("total_orders", 0)),
                "lowest_selling_products": [{"name": p["name"], "sales": p["sales"]} for p in lowest_sellers],
                "abandoned_carts_count": abandoned_carts
            }
        }

    async def _handle_restock_check(self) -> dict[str, Any]:
        inv = await self.sql_builder.get_inventory_health()
        return {
            "intent": "INVENTORY_RESTOCK",
            "sources": ["Inventory", "Products"],
            "data": {
                "low_stock_count": inv["low_stock_count"],
                "out_of_stock_count": inv["out_of_stock_count"],
                "health_pct": inv["health_pct"],
                "out_of_stock_details": inv["out_of_stock_details"][:5],
                "low_stock_details": inv["low_stock_details"][:5]
            }
        }

    async def _handle_churn_check(self) -> dict[str, Any]:
        customers = await self.intel_service.calculate_rfm_and_segmentation()
        
        # Filter churners
        churn_risk = [
            {
                "customer_name": c["customer_name"],
                "email": c["email"],
                "risk_level": c["churn"]["risk_level"],
                "explanation": c["churn"]["explanation"]
            }
            for c in customers if c["churn"]["risk_level"].lower() in ("high", "medium")
        ][:5]

        return {
            "intent": "CUSTOMER_CHURN",
            "sources": ["Customer Intelligence", "RFM Segmentation"],
            "data": {
                "total_customers_analyzed": len(customers),
                "at_risk_customers_count": len(churn_risk),
                "churn_risk_list": churn_risk
            }
        }

    async def _handle_trending_products(self) -> dict[str, Any]:
        prods = await self.sales_service.get_product_analytics()
        top_selling = prods.get("top_selling", [])[:5]
        return {
            "intent": "TRENDING_PRODUCTS",
            "sources": ["Sales Analytics", "Telemetry Views"],
            "data": {
                "trending_list": [{"name": p["name"], "sales": p["sales"], "rating": p["rating"]} for p in top_selling]
            }
        }

    async def _handle_recommendations_degradation(self) -> dict[str, Any]:
        # Reuse NCF model metrics or return fallback parameters
        import os, json
        precision = 0.048
        ndcg = 0.065
        metrics_path = "models/evaluation_metrics.json"
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r") as f:
                    data = json.load(f)
                    precision = data.get("precision_at_10", precision)
                    ndcg = data.get("ndcg", ndcg)
            except Exception:
                pass
                
        return {
            "intent": "RECOMMENDATION_DEGRADATION",
            "sources": ["NCF Recommendation Engine", "PyTorch Model Registry"],
            "data": {
                "precision_at_10": precision,
                "ndcg": ndcg,
                "status": "Degraded" if precision < 0.05 else "Optimal"
            }
        }

    async def _handle_sentiment_check(self) -> dict[str, Any]:
        csat = await self.sql_builder.get_customer_satisfaction()
        return {
            "intent": "CUSTOMER_SATISFACTION",
            "sources": ["Reviews", "NLP Sentiment Engine"],
            "data": csat
        }

    async def _handle_slow_moving(self) -> dict[str, Any]:
        prods = await self.sales_service.get_product_analytics()
        lowest_selling = prods.get("lowest_selling", [])[:5]
        return {
            "intent": "SLOW_PRODUCTS",
            "sources": ["Sales Analytics", "Inventory"],
            "data": {
                "slow_moving_list": [{"name": p["name"], "stock": p["stock"], "price": p["price"], "sales": p["sales"]} for p in lowest_selling if p["sales"] <= 2]
            }
        }

    async def _handle_kpi_summary(self) -> dict[str, Any]:
        sales = await self.sales_service.get_sales_analytics("today")
        summary = sales.get("summary", {})
        inv = await self.sql_builder.get_inventory_health()
        csat = await self.sql_builder.get_customer_satisfaction()

        return {
            "intent": "KPI_SUMMARY",
            "sources": ["Sales", "Inventory", "Reviews"],
            "data": {
                "revenue_today": float(summary.get("total_revenue", 0.0)),
                "orders_today": int(summary.get("total_orders", 0)),
                "inventory_health_pct": inv["health_pct"],
                "customer_satisfaction_score": csat["satisfaction_score"],
                "positive_reviews_pct": csat["positive_pct"]
            }
        }

    async def _handle_campaigns_performance(self) -> dict[str, Any]:
        # Pull learning outcomes to evaluate campaigns success
        from sqlalchemy import select
        from app.models.agent_learning import AgentLearning
        
        stmt = select(AgentLearning).limit(10)
        res = await self.db.execute(stmt)
        learnings = res.scalars().all()
        
        campaigns = [
            {
                "action_id": l.action_id,
                "roi": l.roi,
                "revenue_before": l.revenue_before,
                "revenue_after": l.revenue_after,
                "success": l.success
            }
            for l in learnings
        ]

        return {
            "intent": "CAMPAIGN_PERFORMANCE",
            "sources": ["AgentLearning", "Campaigns Analytics"],
            "data": {
                "campaigns_list": campaigns,
                "average_roi": sum([c["roi"] for c in campaigns]) / len(campaigns) if campaigns else 0.0
            }
        }

    async def _handle_report_generation(self) -> dict[str, Any]:
        return {
            "intent": "REPORT_GENERATION",
            "sources": ["System Analytics", "Executive Summary"],
            "data": {"requested_report": "weekly"}
        }

    async def _handle_default_analytics(self) -> dict[str, Any]:
        sales = await self.sales_service.get_sales_analytics("last_30_days")
        summary = sales.get("summary", {})
        return {
            "intent": "DEFAULT_SEARCH",
            "sources": ["Storefront Database"],
            "data": {
                "revenue_30d": float(summary.get("total_revenue", 0.0)),
                "orders_30d": int(summary.get("total_orders", 0))
            }
        }
