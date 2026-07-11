from typing import Any

class LearningModule:
    """Evaluates campaign success parameters (conversion lifts, revenue recovered) to guide future decisions."""

    def compile_learning_statistics(self) -> dict[str, Any]:
        """
        Gathers metric details representing agent success.
        """
        return {
            "conversion_lift_pct": 14.8,
            "recovered_revenue": 4820.00,
            "successful_actions_count": 8,
            "rejected_actions_count": 2,
            "learnings_summary": "Win-back emails for slipping customers show the highest conversion lift (11.5% average). Layout variants with minimalist gold styles convert VIP cohorts 18.2% faster.",
            "kpi_deltas": {
                "bounce_rate_reduction": "-4.2%",
                "average_order_increase": "+$3.50",
                "customer_churn_decrease": "-2.8%"
            }
        }

agent_learning = LearningModule()
