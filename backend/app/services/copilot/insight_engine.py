from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.copilot.sql_builder import CopilotSqlBuilder
from app.services.analytics.sales_product import SalesProductAnalyticsService
from app.services.analytics.customer_intelligence import CustomerIntelligenceService


class CopilotInsightEngine:
    """Detects retail anomalies, tracks operational risks, and proposes corrective actions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sql_builder = CopilotSqlBuilder(db)
        self.sales_service = SalesProductAnalyticsService(db)
        self.intel_service = CustomerIntelligenceService(db)

    async def generate_business_insights(self) -> list[dict[str, Any]]:
        """Retrieve insights detailing anomalies and direct business recommendations."""
        insights = []
        
        # 1. Check stockouts
        inv = await self.sql_builder.get_inventory_health()
        if inv["out_of_stock_count"] > 0:
            insights.append({
                "type": "inventory",
                "title": "Critical Stockout Anomaly",
                "description": f"Currently, {inv['out_of_stock_count']} product(s) are completely out of stock, causing immediate revenue loss.",
                "recommendation": "Launch emergency restock supplier orders and verify supplier lead times.",
                "priority": "HIGH"
            })

        # 2. Check low stock
        if inv["low_stock_count"] > 0:
            insights.append({
                "type": "inventory",
                "title": "Low Inventory Alert",
                "description": f"{inv['low_stock_count']} products have dipped below critical buffer levels (stock < 5).",
                "recommendation": "Create stock replenishment request to prevent complete depletion.",
                "priority": "MEDIUM"
            })

        # 3. Check customer satisfaction
        csat = await self.sql_builder.get_customer_satisfaction()
        if csat["positive_pct"] < 80.0:
            insights.append({
                "type": "sentiment",
                "title": "Customer Satisfaction Warning",
                "description": f"Positive review rating percentage has dropped to {csat['positive_pct']}% of total sentiment logs.",
                "recommendation": "Identify products with low rating scores and implement support outreach campaigns.",
                "priority": "HIGH"
            })

        # 4. Check payment failures
        pay = await self.sql_builder.get_payment_failures()
        if pay["payment_failure_rate"] > 5.0:
            insights.append({
                "type": "payments",
                "title": "Payment Gateway Failures",
                "description": f"Recent checkout payment failure rate is high ({pay['payment_failure_rate']}%).",
                "recommendation": "Verify stripe/paypal webhook integrations and inspect failed log payloads.",
                "priority": "HIGH"
            })

        # 5. Check cart abandonment
        abandoned_carts = await self.sql_builder.get_abandoned_carts_count()
        if abandoned_carts >= 5:
            insights.append({
                "type": "cart",
                "title": "Cart Abandonment Spike",
                "description": f"Currently, {abandoned_carts} users have items sitting in active carts for over 2 hours without checking out.",
                "recommendation": "Generate win-back cart coupons and dispatch nudge reminders.",
                "priority": "MEDIUM"
            })

        # If empty, add default system health insight
        if not insights:
            insights.append({
                "type": "operations",
                "title": "Operational Health Optimal",
                "description": "Telemetry scan confirms all stock levels, payment completions, and sales pipelines are within buffer bounds.",
                "recommendation": "No urgent actions required. Maintain baseline schedules.",
                "priority": "LOW"
            })

        return insights

    async def get_business_risks(self) -> list[dict[str, Any]]:
        """Compiles operational risks categorized by threat levels and calculates a business risk index score."""
        insights = await self.generate_business_insights()
        
        risks = []
        for ins in insights:
            if ins["priority"] in ("HIGH", "MEDIUM"):
                risks.append({
                    "category": ins["type"].upper(),
                    "threat": ins["title"],
                    "description": ins["description"],
                    "impact": "High Risk of Revenue Loss" if ins["priority"] == "HIGH" else "Medium Operational Strain",
                    "action": ins["recommendation"],
                    "severity": ins["priority"]
                })

        return risks

    async def calculate_business_risk_score(self) -> int:
        """Calculates a global risk score (0-100 scale) based on telemetry warnings."""
        score = 10  # baseline
        
        inv = await self.sql_builder.get_inventory_health()
        csat = await self.sql_builder.get_customer_satisfaction()
        pay = await self.sql_builder.get_payment_failures()
        
        # Increments based on issues
        score += inv["out_of_stock_count"] * 10
        score += inv["low_stock_count"] * 3
        
        if csat["positive_pct"] < 80.0:
            score += int((80.0 - csat["positive_pct"]) * 1.5)
            
        if pay["payment_failure_rate"] > 5.0:
            score += int(pay["payment_failure_rate"] * 2)

        # Cap at 100
        return min(score, 100)
