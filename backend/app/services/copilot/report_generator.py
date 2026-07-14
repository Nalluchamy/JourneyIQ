import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.copilot.sql_builder import CopilotSqlBuilder
from app.services.copilot.insight_engine import CopilotInsightEngine
from app.services.analytics.sales_product import SalesProductAnalyticsService
from app.services.analytics.customer_intelligence import CustomerIntelligenceService


class CopilotReportGenerator:
    """Compiles daily, weekly, and monthly performance reports for data extraction or download."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sql_builder = CopilotSqlBuilder(db)
        self.insight_engine = CopilotInsightEngine(db)
        self.sales_service = SalesProductAnalyticsService(db)
        self.intel_service = CustomerIntelligenceService(db)

    async def generate_report_data(self, report_type: str) -> dict[str, Any]:
        """Query database metrics and assemble a comprehensive report dictionary."""
        report_type = report_type.lower()
        days = 1 if report_type == "daily" else (7 if report_type == "weekly" else 30)

        # 1. Fetch Sales and Revenue summaries
        sales = await self.sales_service.get_sales_analytics(f"last_{days}_days" if days > 1 else "today")
        summary = sales.get("summary", {})
        
        # 2. Fetch inventory health
        inv = await self.sql_builder.get_inventory_health()
        
        # 3. Fetch satisfaction sentiment
        csat = await self.sql_builder.get_customer_satisfaction()
        
        # 4. Fetch customer segment details
        customers = await self.intel_service.calculate_rfm_and_segmentation()
        vip_count = len([c for c in customers if c["segment"].lower() in ("vip", "champions")])
        at_risk_count = len([c for c in customers if c["churn"]["risk_level"].lower() in ("high", "medium")])

        # 5. Fetch operational risks and actions
        risks = await self.insight_engine.get_business_risks()
        risk_score = await self.insight_engine.calculate_business_risk_score()

        # 6. Fetch recent agent decisions
        from sqlalchemy import select
        from app.models.agent_action import AgentAction
        stmt = select(AgentAction).order_by(AgentAction.created_at.desc()).limit(5)
        res_actions = await self.db.execute(stmt)
        decisions = [
            {"title": a.title, "status": a.status, "date": a.created_at.strftime("%Y-%m-%d")}
            for a in res_actions.scalars().all()
        ]

        report_title = f"{report_type.capitalize()} Business Executive Report"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "title": report_title,
            "type": report_type,
            "timestamp": timestamp,
            "summary": {
                "total_revenue": float(summary.get("total_revenue", 0.0)),
                "orders_count": int(summary.get("total_orders", 0)),
                "average_order_value": float(summary.get("average_order_value", 0.0)),
                "conversion_rate_pct": float(summary.get("conversion_rate", 2.8) if summary.get("conversion_rate") else 2.8)
            },
            "inventory": {
                "health_pct": inv["health_pct"],
                "low_stock_count": inv["low_stock_count"],
                "out_of_stock_count": inv["out_of_stock_count"]
            },
            "customers": {
                "total_customers": len(customers),
                "vip_segments_count": vip_count,
                "at_risk_segments_count": at_risk_count
            },
            "sentiment": {
                "customer_satisfaction_score": csat["satisfaction_score"],
                "positive_reviews_pct": csat["positive_pct"]
            },
            "risks_and_actions": {
                "risk_score": risk_score,
                "threats": risks[:5]
            },
            "autonomous_agent_decisions": decisions
        }

    async def generate_markdown_report(self, report_type: str) -> str:
        """Format the report dictionary into clear, readable Markdown."""
        data = await self.generate_report_data(report_type)
        
        md = f"""# 📊 {data['title']}
Generated at: `{data['timestamp']}`
---

## 📈 Executive Sales Summary
* **Total Revenue**: ₹{data['summary']['total_revenue']:,.2f}
* **Total Confirmed Orders**: {data['summary']['orders_count']} orders
* **Average Order Value (AOV)**: ₹{data['summary']['average_order_value']:,.2f}
* **Storefront Conversion Rate**: {data['summary']['conversion_rate_pct']}%

---

## 📦 Inventory Status
* **Inventory Health Score**: {data['inventory']['health_pct']}%
* **Out of Stock Items**: {data['inventory']['out_of_stock_count']}
* **Low Stock Items Alert**: {data['inventory']['low_stock_count']}

---

## 👥 Customer Intelligence
* **Total Tracked Shoppers**: {data['customers']['total_customers']}
* **VIP Core Segments**: {data['customers']['vip_segments_count']} customers
* **At-Risk / Slipping Cohorts**: {data['customers']['at_risk_segments_count']} customers

---

## ⭐ Sentiment Insights (CSAT)
* **Customer Satisfaction Rating**: {data['sentiment']['customer_satisfaction_score']}/100
* **Positive Review Ratio**: {data['sentiment']['positive_reviews_pct']}%

---

## ⚠️ Operational Risks & Action Plans (Risk Score: {data['risks_and_actions']['risk_score']}/100)
"""
        if not data['risks_and_actions']['threats']:
            md += "* No high-severity operational risks detected in this period.\n"
        else:
            for idx, r in enumerate(data['risks_and_actions']['threats']):
                md += f"""### {idx+1}. [{r['severity']}] {r['threat']}
* **Area**: {r['category']}
* **Details**: {r['description']}
* **Operational Impact**: {r['impact']}
* **Recommended Action**: {r['action']}

"""

        md += "\n---\n## 🤖 Autonomous Agent Decisions Log\n"
        if not data['autonomous_agent_decisions']:
            md += "* No decisions dispatched in this period.\n"
        else:
            for d in data['autonomous_agent_decisions']:
                md += f"* `{d['date']}` | **{d['title']}** — Status: `{d['status']}`\n"

        return md
