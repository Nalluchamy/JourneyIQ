from typing import Any

class PlanningModule:
    """Translates reasoning findings into actionable plans, identifying safety-critical actions."""

    def construct_plans(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Build plans based on identified anomalies.
        """
        plans = []
        
        for idx, f in enumerate(findings):
            anomaly = f["anomaly"]
            
            if anomaly == "High Cart Abandonment":
                plans.append({
                    "id": f"action-{idx+1}",
                    "title": "Trigger win-back coupon to Slipping customers",
                    "description": "Send a automated 20% discount coupon to customers who haven't completed checkout in the last 48 hours.",
                    "requires_approval": True,
                    "target_segment": "At-Risk Customers",
                    "impact": "Expected to recover 12% of abandoned checkouts."
                })
                plans.append({
                    "id": f"action-{idx+1.5}",
                    "title": "A/B test vibrant checkout layout",
                    "description": "Launch visual variant of the storefront featuring prominent buttons to increase conversion rates.",
                    "requires_approval": False,
                    "target_segment": "All Visitors",
                    "impact": "Expected to improve layout conversion by 2%."
                })
                
            elif anomaly == "Product Stockout Risk":
                plans.append({
                    "id": f"action-{idx+2}",
                    "title": "Email stock replenishment alert",
                    "description": "Notify supply warehouse managers to reorder low stock products.",
                    "requires_approval": False,
                    "target_segment": "Operations",
                    "impact": "Ensure item availability."
                })
                
            elif anomaly == "Declining Customer Sentiment":
                plans.append({
                    "id": f"action-{idx+3}",
                    "title": "Launch customer feedback follow-up campaign",
                    "description": "Send feedback emails to buyers who rated products negatively to resolve customer issues.",
                    "requires_approval": True,
                    "target_segment": "Dissatisfied Customers",
                    "impact": "Improve storefront customer satisfaction ratings."
                })

        return plans
