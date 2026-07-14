from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.copilot.sql_builder import CopilotSqlBuilder
from app.services.copilot.insight_engine import CopilotInsightEngine
from app.services.analytics.sales_product import SalesProductAnalyticsService


class CopilotExecutiveSummary:
    """Compiles dashboard executive summaries containing business risks, suggested actions, and key retail metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.sql_builder = CopilotSqlBuilder(db)
        self.insight_engine = CopilotInsightEngine(db)
        self.sales_service = SalesProductAnalyticsService(db)

    async def get_executive_summary_dashboard(self) -> dict[str, Any]:
        """Fetch all dashboard KPI cards, risks list, and proposed actions."""
        sales = await self.sales_service.get_sales_analytics("last_30_days")
        summary = sales.get("summary", {})
        
        inv = await self.sql_builder.get_inventory_health()
        csat = await self.sql_builder.get_customer_satisfaction()
        
        # Pull NCF model metrics or return fallback defaults
        import os, json
        precision = 0.048
        metrics_path = "models/evaluation_metrics.json"
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r") as f:
                    data = json.load(f)
                    precision = data.get("precision_at_10", precision)
            except Exception:
                pass
                
        # Count agent actions
        from sqlalchemy import select
        from app.models.agent_action import AgentAction
        stmt_decisions = select(AgentAction)
        res_decisions = await self.db.execute(stmt_decisions)
        decisions = res_decisions.scalars().all()
        completed_decisions = len([d for d in decisions if d.status == "COMPLETED"])

        # Operational risks
        risks = await self.insight_engine.get_business_risks()
        risk_score = await self.insight_engine.calculate_business_risk_score()

        # Compile suggested actions
        insights = await self.insight_engine.generate_business_insights()
        suggested_actions = [
            {"id": idx + 1, "insight": ins["description"], "action": ins["recommendation"], "severity": ins["priority"]}
            for idx, ins in enumerate(insights)
        ]

        return {
            "kpi_cards": {
                "total_revenue": float(summary.get("total_revenue", 0.0)),
                "confirmed_orders": int(summary.get("total_orders", 0)),
                "conversion_rate_pct": float(summary.get("conversion_rate", 2.8) if summary.get("conversion_rate") else 2.8),
                "customer_satisfaction_score": csat["satisfaction_score"],
                "inventory_health_pct": inv["health_pct"],
                "recommendation_accuracy_pct": round(precision * 100, 1),
                "agent_decisions_count": completed_decisions,
                "business_risk_score": risk_score
            },
            "business_risks": risks,
            "suggested_actions": suggested_actions
        }
